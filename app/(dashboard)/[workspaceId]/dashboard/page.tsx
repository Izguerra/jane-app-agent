import { redirect } from 'next/navigation';

export default async function DashboardPage({ params }: { params: Promise<{ workspaceId: string }> }) {
  const { workspaceId } = await params;
  redirect(`/${workspaceId}/dashboard/analytics`);
}
