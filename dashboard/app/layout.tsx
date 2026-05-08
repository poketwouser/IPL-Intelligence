import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "IPL Analytics — Premium Cricket Intelligence Platform",
  description: "World-class IPL analytics dashboard with 17 seasons of cricket data, advanced metrics, and stunning visualizations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-[#0a0e1a] antialiased">
        <Sidebar />
        <main className="lg:ml-[240px] min-h-screen particles-bg">
          <div className="px-4 lg:px-8 py-6 max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
