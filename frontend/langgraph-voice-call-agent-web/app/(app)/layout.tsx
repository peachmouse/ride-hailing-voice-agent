import { headers } from 'next/headers';
import Image from 'next/image';
import Link from 'next/link';

import { getAppConfig } from '@/lib/utils';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default async function AppLayout({ children }: AppLayoutProps) {
  const hdrs = await headers();
  const { appName, logo } = await getAppConfig(hdrs);

  return (
    <>
      <header className="fixed top-0 left-0 z-50 hidden w-full flex-row items-center justify-between p-6 md:flex">
        <Link
          href="/"
          className="text-foreground flex items-center gap-3"
        >
          {logo && <Image src={logo} alt={appName} width={56} height={56} />}
          <Image src="/freenow-logo.svg" alt="FreeNow" width={180} height={52} />
        </Link>
      </header>
      {children}
    </>
  );
}
