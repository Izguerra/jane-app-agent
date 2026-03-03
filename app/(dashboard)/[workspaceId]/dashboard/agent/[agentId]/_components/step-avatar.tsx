"use client";

import { AgentFormData } from "./types";
import { AvatarSelector } from "../../_components/avatar-selector";

interface StepAvatarProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function StepAvatar({ formData, setFormData }: StepAvatarProps) {
    return <AvatarSelector formData={formData} setFormData={setFormData} showTitle={true} />;
}
