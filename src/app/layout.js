import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import { Toaster } from "react-hot-toast";
import { Inter } from 'next/font/google';
import FooterVisibility from "./components/FooterVisibility";


const inter = Inter({ subsets: ['latin'] });

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata = {
  title: "ConformIT",
  description: "Évaluation documentaire et conformité — scores de risque explicables",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body className={`${geistSans.variable} ${inter.variable} antialiased bg-gray-50 text-gray-800`}>
        <AuthProvider>
          <Toaster position="top-right" />

          <div className="flex min-h-dvh flex-col">
            <div className="min-w-0 flex-1">
              {children}
            </div>
            <FooterVisibility />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
