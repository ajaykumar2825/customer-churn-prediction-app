import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import "./globals.css";
import { Providers } from "@/components/providers";
import { Shell } from "@/components/shell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Churn Intelligence — Customer Churn Prediction Platform",
    template: "%s · Churn Intelligence",
  },
  description:
    "Enterprise customer churn prediction platform powered by gradient-boosted machine learning, SHAP explanations and executive business analytics.",
  keywords: ["churn prediction", "customer retention", "machine learning", "SHAP", "XGBoost"],
  openGraph: {
    title: "Churn Intelligence",
    description: "Predict customer churn before it happens. Explain why. Act with confidence.",
    type: "website",
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"),
};

export const viewport: Viewport = {
  themeColor: "#050816",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Providers>
          <Shell>{children}</Shell>
        </Providers>
      </body>
    </html>
  );
}