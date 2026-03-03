"use client";

import { useParams } from "next/navigation";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function useWorkspace() {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;

    const { data: workspace, error, isLoading } = useSWR(
        workspaceId ? `/api/workspaces/${workspaceId}` : null,
        fetcher
    );

    return {
        workspace,
        workspaceId,
        isLoading,
        error
    };
}
