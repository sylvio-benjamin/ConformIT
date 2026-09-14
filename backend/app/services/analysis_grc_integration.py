"""
Service d'intégration entre les analyses et le module GRC.
Extrait les findings des analyses et crée/met à jour les risques dans la GRC.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID as PyUUID
import logging

from app.models.analyses import Analysis
from app.models.risks import Risk, RiskAssessment, RiskScore
from app.models.analysis_risk_link import AnalysisRiskLink, RiskHistory
from app.models.organizations import Organization, User

logger = logging.getLogger(__name__)


class AnalysisGRCIntegrationService:
    """Service pour intégrer les analyses avec la GRC."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_findings_from_analysis(self, analysis: Analysis) -> List[Dict[str, Any]]:
        """
        Extrait les findings (risques, anomalies, non-conformités) d'une analyse.
        
        Args:
            analysis: Objet Analysis à analyser
            
        Returns:
            Liste de findings structurés
        """
        findings = []
        
        # Trouver les questions/réponses qui indiquent des risques
        details = analysis.details or []
        
        # Scoring basé sur le score total et le niveau de risque
        score = analysis.total_score or 0
        risk_level = (analysis.risk_level or "").lower()
        
        # Déterminer la criticité basée sur le score et le niveau de risque
        if score >= 80 or risk_level in ['critical', 'high']:
            severity = "critical"
        elif score >= 60 or risk_level == 'medium':
            severity = "high"
        elif score >= 40:
            severity = "medium"
        else:
            severity = "low"
        
        # Si le score est élevé ou le risque critique, créer un finding global
        if score > 40 or risk_level in ['high', 'critical']:
            finding_description = self._generate_finding_description(analysis, details)
            
            findings.append({
                "type": "risk",
                "severity": severity,
                "title": f"Risque détecté dans l'analyse de {analysis.company_name}",
                "description": finding_description,
                "analysis_score": score,
                "analysis_risk_level": analysis.risk_level,
                "document_type": analysis.document_type,
                "company_name": analysis.company_name,
                "rcs": analysis.rcs,
                "details": details[:5]  # Limiter aux 5 premières questions pour éviter la surcharge
            })
        
        # Analyser les détails pour trouver des non-conformités spécifiques
        for detail in details:
            if isinstance(detail, dict):
                question = detail.get("question", "")
                reponse = detail.get("reponse", "").lower()
                justification = detail.get("justification", "")
                
                # Détecter les réponses qui indiquent des problèmes
                if any(keyword in reponse for keyword in ['non', 'ne pas', 'manque', 'absent', 'pas de', 'aucun']):
                    findings.append({
                        "type": "non_compliance",
                        "severity": "medium",
                        "title": f"Non-conformité détectée: {question[:100]}",
                        "description": f"Question: {question}\nRégulation: {reponse}\nJustification: {justification}",
                        "analysis_score": score,
                        "analysis_risk_level": analysis.risk_level,
                        "question": question,
                        "reponse": reponse,
                        "justification": justification
                    })
        
        return findings
    
    def _generate_finding_description(self, analysis: Analysis, details: List[Dict]) -> str:
        """Génère une description de finding basée sur l'analyse."""
        description_parts = [
            f"Analyse réalisée sur {analysis.company_name}",
            f"Type de document: {analysis.document_type or 'Non spécifié'}",
            f"Score total: {analysis.total_score}/100",
            f"Niveau de risque: {analysis.risk_level or 'Non spécifié'}",
        ]
        
        if analysis.rcs:
            description_parts.append(f"RCS: {analysis.rcs}")
        
        if details:
            issues = [d for d in details if isinstance(d, dict) and 'non' in str(d.get('reponse', '')).lower()]
            if issues:
                description_parts.append(f"\n{len(issues)} non-conformité(s) détectée(s)")
        
        return "\n".join(description_parts)
    
    def find_similar_risks(self, finding: Dict[str, Any], organization_id: PyUUID) -> List[Risk]:
        """
        Trouve les risques similaires existants dans la GRC.
        
        Args:
            finding: Finding extrait de l'analyse
            organization_id: ID de l'organisation
            
        Returns:
            Liste de risques similaires
        """
        # Rechercher par titre similaire
        title_keywords = finding.get("title", "").lower().split()[:3]  # Prendre les 3 premiers mots
        
        # Rechercher par description similaire
        description = finding.get("description", "").lower()
        
        # Rechercher par entreprise (si RCS disponible)
        company_name = finding.get("company_name", "").lower()
        
        # Recherche dans les risques existants de l'organisation
        query = self.db.query(Risk).filter(
            Risk.organization_id == organization_id,
            Risk.status != "closed"  # Ignorer les risques fermés
        )
        
        similar_risks = []
        for risk in query.all():
            similarity_score = 0
            
            # Vérifier le titre
            risk_title = (risk.title or "").lower()
            if any(keyword in risk_title for keyword in title_keywords if len(keyword) > 3):
                similarity_score += 3
            
            # Vérifier la description
            risk_desc = (risk.description or "").lower()
            if any(keyword in risk_desc for keyword in title_keywords if len(keyword) > 3):
                similarity_score += 2
            
            # Vérifier le nom de l'entreprise dans les métadonnées
            if risk.meta_data:
                meta_company = str(risk.meta_data.get("company_name", "")).lower()
                if company_name and company_name in meta_company:
                    similarity_score += 5
            
            # Vérifier le niveau de criticité similaire
            finding_severity = finding.get("severity", "").lower()
            risk_priority = (risk.priority or "").lower()
            if finding_severity == risk_priority:
                similarity_score += 2
            
            # Si score de similarité >= 5, considérer comme similaire
            if similarity_score >= 5:
                similar_risks.append((risk, similarity_score))
        
        # Trier par score de similarité décroissant
        similar_risks.sort(key=lambda x: x[1], reverse=True)
        
        return [risk for risk, _ in similar_risks]
    
    def generate_risk_code(self, organization_id: PyUUID) -> str:
        """Génère un code unique pour un nouveau risque (RISK-001, RISK-002, etc.)."""
        # Compter les risques existants pour cette organisation
        count = self.db.query(func.count(Risk.id)).filter(
            Risk.organization_id == organization_id
        ).scalar()
        
        return f"RISK-{count + 1:03d}"
    
    def create_or_update_risk_from_analysis(
        self,
        analysis: Analysis,
        finding: Dict[str, Any],
        user: User,
        similar_risks: Optional[List[Risk]] = None
    ) -> Tuple[Risk, bool]:
        """
        Crée un nouveau risque ou met à jour un risque existant à partir d'une analyse.
        
        Args:
            analysis: Analyse source
            finding: Finding extrait
            user: Utilisateur qui a créé l'analyse
            similar_risks: Liste de risques similaires (si fournie, utilise le premier)
            
        Returns:
            Tuple (Risk, bool) - Le risque (créé ou mis à jour) et True si créé, False si mis à jour
        """
        organization_id = analysis.organization_id
        
        # Si des risques similaires existent, mettre à jour le premier
        if similar_risks and len(similar_risks) > 0:
            risk = similar_risks[0]
            is_new = False
            
            # Mettre à jour le risque
            old_priority = risk.priority
            old_status = risk.status
            
            # Mettre à jour la priorité si la nouvelle est plus élevée
            severity_mapping = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
            finding_priority = severity_mapping.get(finding.get("severity", "low"), "low")
            priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            
            if priority_order.get(finding_priority, 0) > priority_order.get(old_priority or "low", 0):
                risk.priority = finding_priority
                risk.status = "assessed"  # Passer à assessed si la priorité augmente
            
            # Ajouter à l'historique des analyses
            history_entry = {
                "analysis_id": str(analysis.id),
                "date": datetime.utcnow().isoformat(),
                "score": analysis.total_score,
                "risk_level": analysis.risk_level,
                "finding_severity": finding.get("severity"),
                "company_name": analysis.company_name
            }
            
            current_history = risk.analysis_history or []
            if not isinstance(current_history, list):
                current_history = []
            current_history.append(history_entry)
            risk.analysis_history = current_history
            risk.linked_analyses_count = len(current_history)
            
            # Mettre à jour les métadonnées
            if not risk.meta_data:
                risk.meta_data = {}
            risk.meta_data["last_analysis_id"] = str(analysis.id)
            risk.meta_data["last_analysis_date"] = datetime.utcnow().isoformat()
            risk.meta_data["last_analysis_score"] = analysis.total_score
            
            # Créer un enregistrement d'historique
            if old_priority != risk.priority or old_status != risk.status:
                history = RiskHistory(
                    risk_id=risk.id,
                    change_type="linked_analysis",
                    old_value={"priority": old_priority, "status": old_status},
                    new_value={"priority": risk.priority, "status": risk.status},
                    analysis_id=analysis.id,
                    changed_by=user.id,
                    description=f"Risque mis à jour par l'analyse {analysis.slug} - Priorité: {finding_priority}"
                )
                self.db.add(history)
            
            # Si le score de l'analyse est très bas (< 20), considérer la fermeture du risque
            if analysis.total_score and analysis.total_score < 20 and risk.status not in ["closed", "accepted"]:
                old_status_for_close = risk.status
                risk.status = "treated"
                close_history = RiskHistory(
                    risk_id=risk.id,
                    change_type="status_changed",
                    old_value={"status": old_status_for_close},
                    new_value={"status": "treated"},
                    analysis_id=analysis.id,
                    changed_by=user.id,
                    description=f"Risque traité - Score d'analyse: {analysis.total_score}"
                )
                self.db.add(close_history)
        else:
            # Créer un nouveau risque
            is_new = True
            code = self.generate_risk_code(organization_id)
            
            # Mapping de la sévérité vers la priorité
            severity_mapping = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
            priority = severity_mapping.get(finding.get("severity", "low"), "low")
            
            risk = Risk(
                organization_id=organization_id,
                code=code,
                title=finding.get("title", f"Risque détecté - {analysis.company_name}"),
                description=finding.get("description", ""),
                priority=priority,
                status="identified",  # Nouveau risque identifié
                source_analysis_id=analysis.id,
                created_by=user.id,
                owner_id=user.id,  # Assigner à l'utilisateur qui a créé l'analyse
                meta_data={
                    "source": "analysis",
                    "analysis_id": str(analysis.id),
                    "analysis_slug": analysis.slug,
                    "company_name": analysis.company_name,
                    "document_type": analysis.document_type,
                    "rcs": analysis.rcs
                },
                analysis_history=[{
                    "analysis_id": str(analysis.id),
                    "date": datetime.utcnow().isoformat(),
                    "score": analysis.total_score,
                    "risk_level": analysis.risk_level,
                    "finding_severity": finding.get("severity")
                }],
                linked_analyses_count=1
            )
            
            self.db.add(risk)
            self.db.flush()  # Pour obtenir l'ID du risque
            
            # Créer un enregistrement d'historique
            history = RiskHistory(
                risk_id=risk.id,
                change_type="created",
                old_value=None,
                new_value={
                    "priority": priority,
                    "status": "identified",
                    "title": risk.title
                },
                analysis_id=analysis.id,
                changed_by=user.id,
                description=f"Risque créé automatiquement à partir de l'analyse {analysis.slug}"
            )
            self.db.add(history)
        
        # Créer le lien entre l'analyse et le risque
        link = AnalysisRiskLink(
            analysis_id=analysis.id,
            risk_id=risk.id,
            finding_type=finding.get("type", "risk"),
            severity=finding.get("severity", "low"),
            finding_description=finding.get("description", ""),
            finding_details=finding,
            analysis_score=analysis.total_score,
            analysis_risk_level=analysis.risk_level,
            integration_status="created" if is_new else "updated",
            auto_generated=True
        )
        self.db.add(link)
        
        # Créer une évaluation de risque automatique
        assessment = RiskAssessment(
            risk_id=risk.id,
            assessed_by=user.id,
            assessment_date=datetime.utcnow(),
            probability_level=self._map_severity_to_probability(finding.get("severity", "low")),
            impact_level=self._map_severity_to_impact(finding.get("severity", "low")),
            risk_level=finding.get("severity", "low"),
            risk_score=analysis.total_score or 0,
            methodology="quantitative",
            justification=f"Évaluation automatique basée sur l'analyse {analysis.slug}",
            confidence_level=3
        )
        self.db.add(assessment)
        self.db.flush()
        
        # Créer un score de risque
        risk_score = RiskScore(
            risk_id=risk.id,
            assessment_id=assessment.id,
            score=analysis.total_score or 0,
            normalized_score=float(analysis.total_score or 0),
            calculation_method="analysis_based",
            factors={
                "analysis_score": analysis.total_score,
                "analysis_risk_level": analysis.risk_level,
                "finding_severity": finding.get("severity")
            }
        )
        self.db.add(risk_score)
        
        self.db.commit()
        self.db.refresh(risk)
        
        logger.info(f"✅ Risque {'créé' if is_new else 'mis à jour'}: {risk.code} pour l'analyse {analysis.slug}")
        
        return risk, is_new
    
    def _map_severity_to_probability(self, severity: str) -> int:
        """Mappe la sévérité vers un niveau de probabilité (1-5)."""
        mapping = {"critical": 5, "high": 4, "medium": 3, "low": 2}
        return mapping.get(severity.lower(), 3)
    
    def _map_severity_to_impact(self, severity: str) -> int:
        """Mappe la sévérité vers un niveau d'impact (1-5)."""
        mapping = {"critical": 5, "high": 4, "medium": 3, "low": 2}
        return mapping.get(severity.lower(), 3)
    
    def integrate_analysis_to_grc(
        self,
        analysis_id: str,
        user_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Intègre une analyse dans la GRC en créant ou mettant à jour les risques.
        
        Args:
            analysis_id: ID (slug) ou UUID de l'analyse
            user_id: UUID utilisateur (JWT)
            force: Si True, force la réintégration même si déjà intégrée
            
        Returns:
            Dictionnaire avec les résultats de l'intégration
        """
        # Récupérer l'analyse
        if isinstance(analysis_id, str) and len(analysis_id) > 20:
            # C'est un UUID
            analysis = self.db.query(Analysis).filter(Analysis.id == PyUUID(analysis_id)).first()
        else:
            # C'est un slug
            analysis = self.db.query(Analysis).filter(Analysis.slug == analysis_id).first()
        
        if not analysis:
            raise ValueError(f"Analyse non trouvée: {analysis_id}")
        
        # Vérifier si déjà intégrée
        if not force:
            existing_links = self.db.query(AnalysisRiskLink).filter(
                AnalysisRiskLink.analysis_id == analysis.id
            ).count()
            if existing_links > 0:
                logger.info(f"⚠️ Analyse {analysis.slug} déjà intégrée")
                return {
                    "status": "already_integrated",
                    "analysis_id": str(analysis.id),
                    "analysis_slug": analysis.slug,
                    "existing_links": existing_links
                }
        
        from app.services.plan_service import _find_user
        user = _find_user(self.db, user_id)
        if not user:
            raise ValueError(f"Utilisateur non trouvé: {user_id}")
        
        # Extraire les findings
        findings = self.extract_findings_from_analysis(analysis)
        
        if not findings:
            logger.info(f"ℹ️ Aucun finding détecté dans l'analyse {analysis.slug}")
            return {
                "status": "no_findings",
                "analysis_id": str(analysis.id),
                "analysis_slug": analysis.slug,
                "message": "Aucun risque détecté dans cette analyse"
            }
        
        # Traiter chaque finding
        created_risks = []
        updated_risks = []
        
        for finding in findings:
            # Trouver des risques similaires
            similar_risks = self.find_similar_risks(finding, analysis.organization_id)
            
            # Créer ou mettre à jour le risque
            risk, is_new = self.create_or_update_risk_from_analysis(
                analysis, finding, user, similar_risks
            )
            
            if is_new:
                created_risks.append({
                    "risk_id": str(risk.id),
                    "risk_code": risk.code,
                    "title": risk.title
                })
            else:
                updated_risks.append({
                    "risk_id": str(risk.id),
                    "risk_code": risk.code,
                    "title": risk.title
                })
        
        return {
            "status": "success",
            "analysis_id": str(analysis.id),
            "analysis_slug": analysis.slug,
            "findings_count": len(findings),
            "created_risks": created_risks,
            "updated_risks": updated_risks,
            "total_risks": len(created_risks) + len(updated_risks)
        }

