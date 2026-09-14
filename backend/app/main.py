import os
import json
import re
import time
import logging
import math
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Body, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
# Extraction IA via mistral_client.py (alias groq_client)

from app.core.permissions import get_current_user, require_upload_permission
from app.core.security import assert_jwt_configured
from app.models.organizations import User
from app.models.analyses import Analysis
from app.services.analyse_service import AnalyseService
from app.schemas import UploadFileValidation  # Import depuis schemas.py (fichier existant)
from app.auth import get_client_ip
from fastapi import Request
from security.uploads.file_upload import validate_upload

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

import unicodedata

from app.analyse import router as analyse_router
from app.stripe_routes import router as stripe_router
from app.stripe_webhook import router as webhook_router
from app.api_keys import router as api_keys_router
from app.plan_routes import router as plan_router
from app.user_routes import router as user_router

# Nouveaux modules API selon l'architecture
from app.api.risks import router as risks_router
from app.api.controls import router as controls_router
from app.api.incidents import router as incidents_router
from app.api.compliance import router as compliance_router
from app.api.kris import router as kris_router
from app.api.reports import router as reports_router
from app.api.integrations import router as integrations_router

from app.parser import detecter_type_document
from app.extraction.coherence import DocumentTypeMismatch
from app.config import BILLING_ENABLED, CORS_ORIGINS
from app.storage import commit, delete_file, exists, file_path, list_namespace, read_json, write_bytes, write_json
from security.middleware import WebSecKitMiddleware

# === Configuration ===
# Extraction IA configurée via mistral_client.py

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

assert_jwt_configured()

app = FastAPI(title="ConformIT API", version="3.0.0")

cors_origins = list(CORS_ORIGINS)

# WebSecKit : headers / HTTPS / CORS (CSRF et rate-limit global désactivés ici).
# Auth JWT (da_access / da_refresh) et rate limits métier restent inchangés.
app.add_middleware(WebSecKitMiddleware, trust_proxy=True)

# CORS Starlette conservé en filet de sécurité (credentials + allow_headers=*).
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Handler d'exceptions global pour s'assurer que CORS est toujours présent
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global qui s'assure que les headers CORS sont toujours présents."""
    from starlette.responses import JSONResponse
    
    # Déterminer l'origine de la requête
    origin = request.headers.get("origin")
    allowed_origin = origin if origin in cors_origins or "*" in cors_origins else None
    
    # Si c'est une HTTPException, on la laisse gérer normalement
    if isinstance(exc, HTTPException):
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    else:
        # Pour les autres exceptions, on retourne une erreur 500
        logger.error(f"Erreur non gérée: {exc}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur"}
        )
    
    # Ajouter les headers CORS manuellement si nécessaire
    if allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Initialiser la base de données PostgreSQL
try:
    from app.database import init_db
    init_db()
    print("[OK] Modèles PostgreSQL enregistrés (schéma = Alembic)")
except Exception as e:
    print(f"[WARN] Erreur lors de l'initialisation PostgreSQL: {e}")
    print("[WARN] Les modules GRC nécessitent PostgreSQL pour fonctionner")

# Initialiser le service d'analyse
analyse_service = AnalyseService()

from app.api.auth import router as auth_router
from app.api.admin_users import router as admin_users_router
from app.api.grc_stats import router as grc_stats_router
from app.api.organization_snapshot import router as org_snapshot_router
from app.api.organization import router as org_profile_router, kb_router
from app.api.analysis_jobs import router as analysis_jobs_router
from app.api.compliance_evidence import router as compliance_evidence_router
from app.api.risk_treatments import router as risk_treatments_router
from app.api.grc_audits import router as grc_audits_router
from app.api.alerts import router as alerts_router
app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(grc_stats_router)
app.include_router(org_snapshot_router)
app.include_router(org_profile_router)
app.include_router(kb_router)
app.include_router(analysis_jobs_router)
app.include_router(compliance_evidence_router)
app.include_router(risk_treatments_router)
app.include_router(grc_audits_router)
app.include_router(alerts_router)
app.include_router(analyse_router)
if BILLING_ENABLED:
    app.include_router(stripe_router)
    app.include_router(webhook_router)
app.include_router(plan_router)
app.include_router(api_keys_router)
app.include_router(user_router)

# Nouveaux routers selon l'architecture
app.include_router(risks_router)
app.include_router(controls_router)
app.include_router(incidents_router)
app.include_router(compliance_router)
app.include_router(kris_router)
app.include_router(reports_router)
app.include_router(integrations_router)

# API Users (PostgreSQL)
from app.api.users import router as users_pg_router
from app.api.analyses import router as analyses_pg_router
from app.api.analysis_grc import router as analysis_grc_router
app.include_router(users_pg_router)
app.include_router(analyses_pg_router)
app.include_router(analysis_grc_router)

@app.get("/")
async def root():
    """Endpoint racine pour vérifier que l'API fonctionne"""
    return {
        "message": "SAE Audit API - Serveur opérationnel",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health/live")
async def health_live():
    from app.core.health import liveness

    return liveness()


@app.get("/health/ready")
async def health_ready():
    from app.core.health import readiness

    payload, code = readiness()
    return JSONResponse(content=payload, status_code=code)


@app.get("/health")
async def health_check():
    from app.core.health import readiness

    payload, code = readiness()
    return JSONResponse(content=payload, status_code=code)

@app.get("/test-auth")
async def test_auth(
    request: Request,
    user: User = Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    return {
        "status": "ok",
        "message": "Authentification réussie",
        "client_ip": client_ip,
        "user_id": str(user.id),
    }

@app.options("/analyser/")
async def options_analyser():
    return JSONResponse(content={"message": "CORS preflight OK"}, status_code=200)

def _org_id(user: User) -> Optional[str]:
    return str(user.organization_id) if getattr(user, "organization_id", None) else None


async def groq_generer_resume(
    resultats_analyse: dict,
    slug: str,
    max_retries: int = 3,
    organization_id: Optional[str] = None,
):
    """
    Génère un résumé via Groq à partir des résultats d'analyse.
    
    Gère les erreurs avec retry et backoff exponentiel.
    
    Args:
        resultats_analyse: Dictionnaire avec les réponses, justifications, resultats, etc.
        slug: Identifiant unique de l'analyse
        max_retries: Nombre maximum de tentatives en cas d'erreur
    """
    import asyncio
    
    # Nettoyage du slug pour obtenir slug_clean
    slug_clean = "".join(c for c in slug.lower() if c.isalnum() or c in ('_', '-'))

    # Les résultats sont déjà calculés dans resultats_analyse
    resultats = resultats_analyse.get("resultats", {})
    
    # Extraire les informations directement depuis resultats_analyse
    infos = {
        "nom": resultats_analyse.get("nom", slug),
        "type": resultats_analyse.get("type", ""),
        "rcs": resultats_analyse.get("rcs", ""),
        "score_total": resultats.get("score_total", 0),
        "risque": resultats.get("niveau_risque", "Medium"),
        "precision": resultats.get("precision", 0.0),
        "details": resultats_analyse.get("details", [])
    }

    prompt = f"""
Voici un tableau de réponses issues d'une analyse de document :

{json.dumps(infos, indent=2, ensure_ascii=False)}

Tu dois produire un résumé structuré au format JSON avec précisément ces champs :
- "nom" : le nom de l'entreprise d'après le nom du fichier fourni
- "type" : la forme juridique (ex : SAS, SARL, etc.)
- "rcs" : le numéro RCS (ou "Non précisé" si absent)
- "risque" : niveau global de risque basé sur le score_total calculé (Low, Medium, High, Critical)
- "qualite" : fiabilité de l'analyse (Élevée, Moyenne, Faible) basée sur la précision
- "details" : liste d'objets contenant {{ "question", "reponse", "justification" }}

Tu dois uniquement répondre en JSON, sans balises ni texte autour.
""".strip()

    # Appel API Groq avec retry
    from app.groq_client import appel_groq_async
    
    json_obj = None
    max_retries_optimized = min(max_retries, 2)  # Max 2 tentatives pour le résumé (non critique)
    for attempt in range(max_retries_optimized):
        try:
            # Appel Groq asynchrone
            content_str, error = await appel_groq_async(
                prompt,
                max_retries=1,  # Un seul retry ici car on gère la boucle externe
                temperature=0.1,
                max_tokens=4096
            )
            
            if error:
                raise Exception(error)
            
            # Nettoyer le JSON (enlever markdown si présent)
            json_str = re.sub(r"^```json|```$", "", content_str.strip(), flags=re.MULTILINE)

            try:
                json_obj = json.loads(json_str)
            except json.JSONDecodeError:
                json_obj = {
                    "erreur": "La réponse de l'IA n'était pas un JSON valide.",
                    "contenu_original": json_str
                }
            
            # Succès, sortir de la boucle
            break
            
        except Exception as e:
            error_str = str(e)
            # Vérifier si c'est une erreur 429 (rate limit)
            if "429" in error_str or "rate limit" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # Backoff exponentiel: 5s, 10s, 20s
                    logger.warning(f"Erreur 429 Groq (tentative {attempt + 1}/{max_retries}). Attente {wait_time}s avant retry...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Erreur 429 Groq après {max_retries} tentatives. Utilisation des données calculées sans résumé IA.")
                    # Créer un JSON basique sans résumé IA
                    json_obj = {}
                    break
            else:
                # Autre erreur, logger et utiliser les données calculées
                logger.error(f"Erreur API Groq: {e}")
                json_obj = {}
                break
    
    # Si json_obj est None ou vide, utiliser les données calculées directement
    if not json_obj:
        json_obj = {}

    # Remplacement force des vraies valeurs calculees (priorite sur le resume IA)
    # Nettoyer la précision pour éviter NaN
    precision_clean = infos.get("precision", 0.0)
    if isinstance(precision_clean, float) and (math.isnan(precision_clean) or math.isinf(precision_clean)):
        precision_clean = 0.0
    
    json_obj["score_total"] = infos.get("score_total", 0)
    json_obj["risque"] = infos.get("risque", "Medium")
    json_obj["precision"] = precision_clean
    json_obj["rcs"] = infos.get("rcs", "Non précisé")
    json_obj["type"] = infos.get("type", "")
    json_obj["nom"] = infos.get("nom", slug)
    json_obj["details"] = infos.get("details", [])
    json_obj["qualite"] = f"{precision_clean}%"
    
    # Ajouter un message si le résumé IA n'a pas pu être généré
    if "erreur" not in json_obj and not json_obj.get("nom"):
        json_obj["note"] = "Résumé généré automatiquement (API Groq temporairement indisponible)"

    # Nettoyer le JSON avant sauvegarde (remplacer tous les NaN)
    json_obj_clean = nettoyer_nan_pour_json(json_obj)
    
    # Sauvegarder le JSON nettoyé
    write_json("audits", f"{slug_clean}.json", json_obj_clean, organization_id=organization_id)

    # Sauvegarder via le service
    from app.models import AnalyseData
    analyse_data = AnalyseData(
        slug=slug_clean,
        nom=slug,
        type=json_obj_clean.get("type", ""),
        rcs=json_obj_clean.get("rcs", ""),
        score_total=json_obj_clean.get("score_total", 0),
        risque=json_obj_clean.get("risque", "Medium"),
        precision=json_obj_clean.get("precision", 0.0),
        qualite=json_obj_clean.get("qualite"),
        details=json_obj_clean.get("details", [])
    )
    analyse_service.sauvegarder_analyse(slug_clean, analyse_data)



@app.get("/document-types/")
async def list_document_types(user: User = Depends(get_current_user)):
    """Catalogue des types sélectionnables. Connaissance, pas moteur."""
    from app.extraction.document_types import public_catalog

    return {"types": public_catalog()}


@app.post("/analyser/")
async def analyser_document(
    request: Request,
    pdf: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    user: User = Depends(require_upload_permission),
):
    """
    Endpoint pour analyser un document PDF.
    
    - Validation de l'authentification (via dépendance FastAPI)
    - Validation du fichier (taille, type MIME, extension)
    - Vérification du quota utilisateur
    - Traitement asynchrone
    
    Args:
        request: Objet Request FastAPI (pour logging IP)
        pdf: Fichier PDF à analyser
        api_key: Clé API validée (via dépendance)
    """
    # L'authentification est déjà vérifiée par la dépendance
    # On peut logger l'IP du client si nécessaire
    from app.core.rate_limit import enforce_analyse

    client_ip = get_client_ip(request)
    if client_ip:
        logger.info(f"Requête d'analyse reçue depuis {client_ip}")
    enforce_analyse(request, user)

    user_id = str(user.id)
    job_id = None
    
    # Si user_id est fourni, vérifier le quota
    if user_id:
        from app.services.plan_service import PlanService
        can_perform, error_message = PlanService.can_perform_analysis(user_id)
        if not can_perform:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Quota dépassé",
                    "message": error_message,
                    "quota": PlanService.get_user_quota(user_id)
                }
            )
    
    # Validation du fichier
    if not pdf.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")
    
    # Valider le type de fichier (extension)
    if not UploadFileValidation.validate_filename(pdf.filename):
        raise HTTPException(
            status_code=400,
            detail="Format de fichier non supporté. Formats acceptés : PDF, CSV, XLS, XLSX."
        )
    
    # Lire le contenu du fichier
    content = await pdf.read()

    # WebSecKit : taille + magic bytes + nom sûr (PDF / CSV / Excel)
    upload_check = validate_upload(content, pdf.filename, pdf.content_type)
    if not upload_check.get("ok"):
        errors = {
            "empty": "Fichier vide.",
            "too-large": f"Fichier trop volumineux. Taille maximale: {UploadFileValidation.MAX_FILE_SIZE / 1024 / 1024} MB",
            "unsafe-name": "Nom de fichier non autorisé.",
            "extension": "Extension de fichier non supportée.",
            "magic": "Le contenu du fichier ne correspond pas à un format autorisé.",
            "ext-mismatch": "L'extension ne correspond pas au contenu du fichier.",
            "mime-mismatch": "Type MIME non autorisé.",
        }
        detail = errors.get(str(upload_check.get("error")), "Fichier rejeté.")
        raise HTTPException(status_code=400, detail=detail)
    
    # Sanitizer le nom de fichier
    filename = UploadFileValidation.sanitize_filename(pdf.filename)
    base_name, extension = os.path.splitext(filename)
    extension = (upload_check.get("extension") or extension or ".pdf")
    extension = str(extension).lower()
    slug = base_name
    slug_clean = "".join(c for c in slug.lower() if c.isalnum() or c in ('_', '-'))

    # Sauvegarder le fichier uploadé (PDF, CSV, Excel) — clé interne, jamais renvoyée au navigateur
    org = _org_id(user)
    storage_name = f"{slug_clean}{extension}"
    storage_key = write_bytes("uploads", storage_name, content, organization_id=org)
    upload_path = str(file_path("uploads", storage_name, organization_id=org))

    from app.services.analysis_job_tracker import attach_analysis, complete_job, fail_job, start_job
    job_id = start_job(
        organization_id=user.organization_id,
        user_id=user.id,
        filename=filename,
        storage_key=storage_key,
        slug=slug_clean,
    )

    selected_type = (document_type or "").strip() or None
    if selected_type:
        from app.extraction.document_types import is_selectable

        if not is_selectable(selected_type):
            fail_job(job_id, "Type de document non supporté")
            raise HTTPException(status_code=400, detail="Type de document non supporté.")
        type_hint = selected_type
        type_source = "user"
        logger.info("[INFO] Type de document fourni par l'utilisateur : %s", type_hint)
    else:
        type_hint = UploadFileValidation.infer_document_type(extension, filename)
        type_source = "inferred"
        if type_hint:
            logger.info("[INFO] Type de document inferé depuis l'extension/nom : %s", type_hint)
        else:
            logger.info("[WARN] Aucun type explicite, detection automatique depuis le contenu")

    # Lancer le traitement + créer résumé + générer PDF
    try:
        # Analyser les questions de manière asynchrone (version optimisée)
        from app.analyse import analyser_questions_async
        from app.extraction.coherence import DocumentTypeMismatch
        
        # Exécuter l'analyse async (FastAPI gère déjà l'event loop)
        resultats_analyse = await analyser_questions_async(
            upload_path,
            type_hint=type_hint,
            type_source=type_source,
        )
        
        # Récupérer le nom de l'entreprise extrait
        nom_entreprise = resultats_analyse.get("nom", slug_clean)
        
        # Générer le slug à partir du nom de l'entreprise (pas du nom de fichier)
        import re
        slug_from_nom = re.sub(r'[^a-z0-9\s-]', '', nom_entreprise.lower())
        slug_from_nom = re.sub(r'\s+', '-', slug_from_nom).strip('-')
        slug_from_nom = slug_from_nom[:50]  # Limiter la longueur
        if not slug_from_nom:
            slug_from_nom = slug_clean
        
        # Utiliser le slug basé sur le nom de l'entreprise
        slug_final = slug_from_nom
        # Construire le JSON final avec les résultats calculés
        resultats_calculs = resultats_analyse.get("resultats", {})
        
        # Construire le JSON complet
        json_final = {
            "nom": nom_entreprise,
            "nom_fichier": filename,  # Nom du fichier original
            "type": resultats_analyse.get("type", ""),
            "rcs": resultats_analyse.get("rcs", ""),
            "score_total": resultats_calculs.get("score_total", 0),
            "risque": resultats_calculs.get("niveau_risque", "Medium"),
            "precision": resultats_calculs.get("precision", 0.0),
            "scores_detail": resultats_calculs.get("scores_detail", {}),
            "details": resultats_analyse.get("details", []),
            "score": resultats_analyse.get("score", resultats_calculs.get("score_total", 0)),
            "risk_color": resultats_analyse.get("risk_color"),
            "document_type": resultats_analyse.get("document_type"),
            "document_type_key": resultats_analyse.get("document_type_key"),
            "slug": slug_final,  # Ajouter le slug au JSON
        }
        
        # Nettoyer les NaN avant sauvegarde
        json_final_clean = nettoyer_nan_pour_json(json_final)
        
        # Sauvegarder le JSON avec le slug basé sur le nom de l'entreprise
        write_json("audits", f"{slug_final}.json", json_final_clean, organization_id=org)
        
        # Générer le résumé avec Groq (optionnel - peut être désactivé si trop d'erreurs)
        # Le résumé IA est optionnel, les données calculées sont déjà disponibles
        try:
            await groq_generer_resume(resultats_analyse, slug_final, organization_id=org)
        except Exception as e:
            logger.warning(f"Résumé Groq non généré (non bloquant): {e}")
            # L'analyse continue sans le résumé IA
        
        # Générer le PDF avec le slug basé sur le nom de l'entreprise
        generer_pdf_depuis_resume(slug_final, organization_id=org)
        complete_job(
            job_id,
            slug=slug_final,
            result_summary={
                "score_total": json_final_clean.get("score_total"),
                "risque": json_final_clean.get("risque"),
                "document_type": json_final_clean.get("document_type"),
            },
            details=json_final_clean.get("details"),
        )
        
        # Si user_id est fourni, incrémenter le compteur et enregistrer l'analyse
        if user_id:
            from app.services.plan_service import PlanService
            PlanService.increment_analysis_count(user_id)
            PlanService.record_analysis(user_id, slug_final, json_final_clean)
            
            # Sauvegarder l'analyse dans PostgreSQL
            try:
                from app.database import SessionLocal
                from app.models.analyses import Analysis, Company, Document
                from app.models.organizations import User, Organization
                from sqlalchemy.orm import Session
                import uuid as uuid_lib
                
                # Créer une session de base de données
                db: Session = SessionLocal()
                
                try:
                    db_user = db.query(User).filter(User.id == user.id).first()
                    if not db_user:
                        raise RuntimeError("Utilisateur authentifié introuvable en base")
                    user = db_user

                    # Récupérer ou créer la compagnie
                    company_id = uuid_lib.uuid4()
                    company_slug = slug_final
                    company = db.query(Company).filter(
                        Company.id == company_id,
                        Company.organization_id == user.organization_id
                    ).first()
                    
                    if not company:
                        company = Company(
                            id=company_id,
                            slug=company_slug,
                            organization_id=user.organization_id,
                            employee_id=user.id,
                            name=nom_entreprise,
                            rcs=json_final_clean.get("rcs", ""),
                            company_type=json_final_clean.get("type", ""),
                            risk=json_final_clean.get("risque", "Medium"),
                            quality=json_final_clean.get("qualite", ""),
                            total_score=json_final_clean.get("score_total", 0),
                            details=json_final_clean.get("details", [])
                        )
                        db.add(company)
                        db.flush()
                    
                    # Importer la fonction pour générer le numéro d'analyse
                    from app.api.analyses import get_next_analysis_id
                    
                    # Vérifier si l'analyse existe déjà
                    existing_analysis = db.query(Analysis).filter(
                        Analysis.slug == slug_final,
                        Analysis.employee_id == user.id
                    ).first()
                    
                    if existing_analysis:
                        logger.info(f"⚠️ Analyse déjà existante dans PostgreSQL: {slug_final}, mise à jour")
                        # Mettre à jour l'analyse existante
                        existing_analysis.company_id = company.id
                        existing_analysis.company_name = nom_entreprise
                        existing_analysis.filename = filename
                        existing_analysis.rcs = json_final_clean.get("rcs", "")
                        existing_analysis.document_type = json_final_clean.get("document_type", "")
                        existing_analysis.risk_level = json_final_clean.get("risque", "Medium")
                        existing_analysis.precision = float(json_final_clean.get("precision", 0.0))
                        existing_analysis.total_score = json_final_clean.get("score_total", 0)
                        existing_analysis.quality = json_final_clean.get("qualite", "")
                        existing_analysis.risk_color = json_final_clean.get("risk_color", "")
                        existing_analysis.status = "Terminée"
                        existing_analysis.details = json_final_clean.get("details", [])
                        analysis = existing_analysis
                    else:
                        # Générer le numéro d'analyse pou(r cet utilisateur (1, 2, 3, etc.)
                        analysis_number = get_next_analysis_id(db, user)
                        logger.info(f"Nouveau numéro d'analyse pour l'utilisateur {user.id}: {analysis_number}")
                        
                        # Créer l'analyse dans PostgreSQL
                        analysis = Analysis(
                            slug=slug_final,
                            analysis_number=analysis_number,  # Numéro d'analyse (1, 2, 3, etc.)
                            organization_id=user.organization_id,
                            employee_id=user.id,
                            company_id=company.id,
                            company_name=nom_entreprise,
                            filename=filename,
                            siret=None,  # Pas encore disponible
                            rcs=json_final_clean.get("rcs", ""),
                            document_type=json_final_clean.get("document_type", ""),
                            risk_level=json_final_clean.get("risque", "Medium"),
                            precision=float(json_final_clean.get("precision", 0.0)),
                            total_score=json_final_clean.get("score_total", 0),
                            quality=json_final_clean.get("qualite", ""),
                            risk_color=json_final_clean.get("risk_color", ""),
                            status="Terminée",
                            details=json_final_clean.get("details", [])
                        )
                        db.add(analysis)
                        db.flush()
                    
                    # Vérifier si le document existe déjà pour cette analyse
                    existing_document = db.query(Document).filter(
                        Document.analysis_id == analysis.id
                    ).first()
                    
                    if not existing_document:
                        # Créer le document associé seulement s'il n'existe pas
                        document = Document(
                            analysis_id=analysis.id,
                            organization_id=user.organization_id,
                            employee_id=user.id,
                            title=filename,
                            content=None,
                            status="finalise",
                            storage_key=storage_key,
                            original_filename=filename,
                            mime_type=pdf.content_type,
                            byte_size=len(content),
                        )
                        db.add(document)
                    
                    db.commit()
                    logger.info(f"✅ Analyse sauvegardée dans PostgreSQL: {slug_final}")
                    attach_analysis(job_id, getattr(analysis, "id", None), slug=slug_final)
                except Exception as e:
                    db.rollback()
                    logger.error(f"❌ Erreur lors de la sauvegarde PostgreSQL: {e}", exc_info=True)
                    # Ne pas bloquer l'analyse si PostgreSQL échoue
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'accès à PostgreSQL: {e}", exc_info=True)
                # Ne pas bloquer l'analyse si PostgreSQL n'est pas disponible
            
            # Récupérer le quota mis à jour pour la réponse
            quota = PlanService.get_user_quota(user_id)
            return {
                "message": "Analyse terminée",
                "slug": slug_final,
                "nom": nom_entreprise,
                "document_type": resultats_analyse.get("document_type"),
                "quota": quota
            }
    except DocumentTypeMismatch as exc:
        fail_job(job_id, exc.message)
        raise HTTPException(status_code=422, detail=exc.message)
    except HTTPException as exc:
        fail_job(job_id, str(getattr(exc, "detail", None) or "HTTP error"))
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
        fail_job(job_id, str(e))
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            media_type="application/json"
        )

    return {"message": "Analyse terminée", "slug": slug_clean}


def nettoyer_nan_pour_json(obj):
    """
    Nettoie un objet Python en remplaçant les valeurs NaN, inf, -inf par None ou 0.
    JSON ne supporte pas ces valeurs spéciales.
    
    Args:
        obj: Objet Python (dict, list, ou valeur primitive)
        
    Returns:
        Objet nettoyé compatible JSON
    """
    import math
    
    if isinstance(obj, dict):
        return {k: nettoyer_nan_pour_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [nettoyer_nan_pour_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return 0.0
        elif math.isinf(obj):
            return 0.0 if obj > 0 else 0.0
        return obj
    else:
        return obj


def _assert_slug_access(db: Session, user: User, slug: str) -> None:
    from app.core.analysis_access import assert_slug_access
    assert_slug_access(db, user, slug)


@app.get("/resultat/{slug}")
def get_resultat(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Récupère le résultat d'une analyse par son slug.
    
    Nettoie automatiquement les valeurs NaN pour éviter les erreurs JSON.
    """
    _assert_slug_access(db, user, slug)
    try:
        data = read_json("audits", f"{slug}.json", organization_id=_org_id(user))
    except Exception as e:
        logger.error(f"Erreur lecture résultat {slug}: {e}")
        return {"terminee": False, "analyseTerminee": False, "error": str(e)}
    if data is None:
        return {"terminee": False, "analyseTerminee": False}
    
    try:
        
        # Nettoyer les valeurs NaN avant de retourner
        data_clean = nettoyer_nan_pour_json(data)
        from app.scoring.engine import attach_breakdown_if_missing
        data_clean = attach_breakdown_if_missing(data_clean)
        data_clean["analyseTerminee"] = True
        
        return data_clean
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de parsing JSON pour {slug}: {e}")
        return {"terminee": False, "analyseTerminee": False, "error": "Fichier JSON invalide"}
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du résultat pour {slug}: {e}")
        return {"terminee": False, "analyseTerminee": False, "error": str(e)}


@app.post("/annuler-analyse/{slug}")
def annuler_analyse(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_slug_access(db, user, slug)
    from app.services.analysis_job_tracker import cancel_job_for_slug
    cancel_job_for_slug(user.organization_id, slug)
    return {"status": "annulation confirmée"}

@app.patch("/modifier-analyse/{slug}")
async def modifier_analyse(
    slug: str,
    data: dict = Body(...),
    user: User = Depends(get_current_user),
):
    """Modifie une analyse (migré vers PostgreSQL via API)."""
    # Déléguer à l'API analyses
    from fastapi import Request
    from app.api.analyses import router as analyses_router
    
    # Cette route est maintenant gérée par /api/analyses/{slug} PUT
    # Garder pour compatibilité, rediriger vers la nouvelle API
    return {
        "message": "Utiliser PUT /api/analyses/{slug} pour modifier une analyse",
        "slug": slug
    }



def generer_pdf_depuis_resume(slug: str, organization_id: Optional[str] = None):
    from textwrap import wrap

    data = read_json("audits", f"{slug}.json", organization_id=organization_id)
    if data is None:
        raise FileNotFoundError("Résumé JSON introuvable")

    pdf_path = str(file_path("pdfs", f"{slug}.pdf", organization_id=organization_id))

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def write_line(text, indent=0, font="Helvetica", size=10, offset=14):
        nonlocal y
        c.setFont(font, size)

        # Gestion retour à la ligne automatique
        max_width = width - 4 * cm - indent
        wrapped_lines = wrap(text, width=int(max_width / (size * 0.5)))

        for line in wrapped_lines:
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm
                c.setFont(font, size)
            c.drawString(2 * cm + indent, y, line)
            y -= offset

    # === TITRE ET INFOS GÉNÉRALES ===
    c.setTitle(f"Audit de {data.get('nom', '')}")
    write_line(f"Rapport d'audit", size=16, font="Helvetica-Bold", offset=24)
    write_line(f"Entreprise : {data.get('nom', '')}", size=12, offset=18)
    write_line(f"Forme juridique : {data.get('type', '')}")
    write_line(f"Numero RCS : {data.get('rcs', '')}")
    write_line(f"Score total : {data.get('score_total', '')}")
    write_line(f"Niveau de risque : {data.get('risque', '')}")
    write_line(f"Qualite de l'analyse : {data.get('precision', '')}")
    write_line("────────────────────────────────────────", offset=20)

    # === DÉTAILS DE L'ANALYSE ===
    write_line("Details des verifications :", font="Helvetica-Bold", size=13, offset=22)

    for idx, detail in enumerate(data.get("details", []), start=1):
        write_line(f"{idx}. {detail['question']}", indent=5, font="Helvetica-Bold", size=11, offset=16)
        write_line(f"→ Réponse : {detail['reponse']}", indent=10)
        write_line(f"→ Justification : {detail['justification']}", indent=10, offset=20)
        write_line("")

    c.save()
    commit("pdfs", f"{slug}.pdf", organization_id=organization_id)
    return pdf_path


def generer_excel_depuis_resume(slug: str, organization_id: Optional[str] = None) -> str:
    """Génère un fichier Excel à partir du résumé JSON."""
    data = read_json("audits", f"{slug}.json", organization_id=organization_id)
    if data is None:
        raise FileNotFoundError("Résumé JSON introuvable")

    excel_path = str(file_path("excels", f"{slug}.xlsx", organization_id=organization_id))

    wb = Workbook()
    ws = wb.active
    ws.title = "Synthèse"

    title_font = Font(bold=True)
    center = Alignment(horizontal="center")

    ws["A1"] = "Entreprise"
    ws["B1"] = data.get("nom", "")
    ws["A2"] = "Forme juridique"
    ws["B2"] = data.get("type", "")
    ws["A3"] = "Numéro RCS"
    ws["B3"] = data.get("rcs", "")
    ws["A4"] = "Score total"
    ws["B4"] = data.get("score_total", "")
    ws["A5"] = "Niveau de risque"
    ws["B5"] = data.get("risque", "")
    ws["A6"] = "Qualité"
    ws["B6"] = data.get("qualite", "")

    for cell in ["A1", "A2", "A3", "A4", "A5", "A6"]:
        ws[cell].font = title_font

    ws["A8"] = "Détails des vérifications"
    ws["A8"].font = Font(bold=True, size=12)

    headers = ["Question", "Réponse", "Justification", "Score"]
    ws.append(headers)
    last_row = ws.max_row
    for idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=last_row, column=idx)
        cell.font = title_font
        cell.alignment = center

    for detail in data.get("details", []):
        ws.append([
            detail.get("question", ""),
            detail.get("reponse", ""),
            detail.get("justification", ""),
            detail.get("score", ""),
        ])

    for col in range(1, 5):
        ws.column_dimensions[get_column_letter(col)].width = 30 if col < 4 else 12

    wb.save(excel_path)
    commit("excels", f"{slug}.xlsx", organization_id=organization_id)
    return excel_path


def to_slug(nom: str) -> str:
    return (
        unicodedata.normalize('NFD', nom)  # <-- important
        .encode('ascii', 'ignore')
        .decode('utf-8')
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

@app.get("/telecharger-pdf/{slug}")
def telecharger_pdf(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Télécharge un PDF d'analyse.
    
    Vérifie que l'utilisateur a accès à la fonctionnalité PDF selon son plan.
    user_id peut être fourni via query parameter ou header X-User-Id.
    """
    _assert_slug_access(db, user, slug)
    from app.services.plan_service import PlanService
    if not PlanService.has_feature(str(user.id), "pdf"):
        raise HTTPException(
            status_code=403,
            detail="Le téléchargement PDF n'est pas disponible avec votre plan. Passez au plan supérieur."
        )
    
    slug_clean = to_slug(slug)
    org = _org_id(user)
    if not exists("pdfs", f"{slug_clean}.pdf", organization_id=org):
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable")
    path_pdf = str(file_path("pdfs", f"{slug_clean}.pdf", organization_id=org))
    return FileResponse(path_pdf, media_type='application/pdf', filename=f"audit_{slug}.pdf")
  
@app.get("/telecharger-excel/{slug}")
def telecharger_excel(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Télécharge un fichier Excel d'analyse.
    
    Vérifie que l'utilisateur a accès à la fonctionnalité Excel selon son plan.
    """
    _assert_slug_access(db, user, slug)
    from app.services.plan_service import PlanService
    if not PlanService.has_feature(str(user.id), "excel"):
        raise HTTPException(
            status_code=403,
            detail="Le téléchargement Excel n'est pas disponible avec votre plan. Passez au plan Pro ou Enterprise."
        )
    
    slug_clean = to_slug(slug)
    org = _org_id(user)
    if not exists("audits", f"{slug_clean}.json", organization_id=org):
        raise HTTPException(status_code=404, detail="Données d'analyse introuvables")

    try:
        generer_excel_depuis_resume(slug_clean, organization_id=org)
    except Exception as e:
        logger.error(f"Erreur génération Excel pour {slug_clean}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération du fichier Excel")

    if not exists("excels", f"{slug_clean}.xlsx", organization_id=org):
        raise HTTPException(status_code=404, detail="Fichier Excel introuvable")
    excel_path = str(file_path("excels", f"{slug_clean}.xlsx", organization_id=org))
    return FileResponse(excel_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=f"analyse_{slug_clean}.xlsx")

@app.delete("/supprimer-fichiers/{slug}")
def supprimer_fichiers(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_slug_access(db, user, slug)
    slug_clean = "".join(c for c in slug.lower() if c.isalnum() or c in ('_', '-'))
    org = _org_id(user)
    erreurs = []
    targets = []
    for ext in UploadFileValidation.ALLOWED_EXTENSIONS:
        targets.append(("uploads", f"{slug_clean}{ext}"))
    targets.extend([
        ("audits", f"{slug_clean}.json"),
        ("pdfs", f"{slug_clean}.pdf"),
        ("excels", f"{slug_clean}.xlsx"),
    ])
    for namespace, name in targets:
        try:
            delete_file(namespace, name, organization_id=org)
        except Exception as e:
            erreurs.append(f"{namespace}/{name} : {e}")
    if erreurs:
        return {"message": "Fichiers partiellement supprimés", "erreurs": erreurs}
    return {"message": "Tous les fichiers supprimés avec succès"}


def detecter_documents_batch():
    for nom_fichier in list_namespace("pdfs"):
        if not nom_fichier.endswith(".pdf"):
            continue
        chemin = str(file_path("pdfs", nom_fichier))
        try:
            type_doc = detecter_type_document(chemin)
            print(f"[INFO] {nom_fichier} => {type_doc}")
        except Exception as e:
            print(f"[ERROR] Erreur avec {nom_fichier} : {e}")


if __name__ == "__main__":
    detecter_documents_batch()