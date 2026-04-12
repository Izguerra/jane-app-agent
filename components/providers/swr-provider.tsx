"use client";

import { SWRConfig } from 'swr';

const fetcher = (url: string) => 
  fetch(url, {
    headers: {
      'Authorization': 'Bearer DEVELOPER_BYPASS'
    }
  }).then(res => res.json());

export function SWRProvider({ 
  children, 
  user, 
  team 
}: { 
  children: React.ReactNode;
  user: any;
  team: any;
}) {
  return (
    <SWRConfig
      value={{
        fetcher,
        fallback: {
          '/api/user': user,
          '/api/team': team
        }
      }}
    >
      {children}
    </SWRConfig>
  );
}
