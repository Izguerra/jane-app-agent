'use client';

import DashboardLayoutComponent from '../dashboard/layout';

export default function CustomersLayout({ children }: { children: React.ReactNode }) {
    return <DashboardLayoutComponent>{children}</DashboardLayoutComponent>;
}
