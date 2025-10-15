export const metadata = {
  title: "Trustiva Swarm",
  description: "Programmatic SEO-ready Next.js shell",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
