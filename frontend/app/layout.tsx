import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DC OPF Simulator',
  description: 'DC Optimal Power Flow Simulator - Build and analyze power systems',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
