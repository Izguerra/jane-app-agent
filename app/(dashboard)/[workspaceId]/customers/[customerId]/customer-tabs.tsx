'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CustomerCommunicationsTab } from './_components/customer-communications-tab';
import { CustomerAppointmentsTab } from './_components/customer-appointments-tab';
import { CustomerCampaignsTab } from './_components/customer-campaigns-tab';
import { CustomerTasksTab } from './_components/customer-tasks-tab';

interface CustomerTabsProps {
    customerId: string;
    workspaceId: string;
}

export function CustomerTabs({ customerId, workspaceId }: CustomerTabsProps) {
    return (
        <Tabs defaultValue="communications" className="w-full">
            <TabsList className="grid w-full grid-cols-5 lg:w-auto">
                <TabsTrigger value="communications">Communications</TabsTrigger>
                <TabsTrigger value="tasks">Tasks & Activity</TabsTrigger>
                <TabsTrigger value="appointments">Appointments</TabsTrigger>
                <TabsTrigger value="calls">Voice Calls</TabsTrigger>
                <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            </TabsList>

            <TabsContent value="communications" className="mt-6">
                <CustomerCommunicationsTab customerId={customerId} />
            </TabsContent>

            <TabsContent value="tasks" className="mt-6">
                <CustomerTasksTab customerId={customerId} />
            </TabsContent>

            <TabsContent value="appointments" className="mt-6">
                <CustomerAppointmentsTab customerId={customerId} workspaceId={workspaceId} />
            </TabsContent>

            <TabsContent value="calls" className="mt-6">
                <CustomerCommunicationsTab customerId={customerId} type="call" />
            </TabsContent>

            <TabsContent value="campaigns" className="mt-6">
                <CustomerCampaignsTab customerId={customerId} />
            </TabsContent>
        </Tabs>
    );
}
