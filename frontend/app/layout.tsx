import './styles.css';
export const metadata = { title: 'AI App Starter' };
export default function RootLayout({ children }: { children: React.ReactNode }){
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <a href="/">Home</a>
          <a href="/chat">Chat</a>
          <a href="/upload">Upload</a>
          <a href="/admin">Admin</a>
        </nav>
        <div className="container">{children}</div>
      </body>
    </html>
  );
}
