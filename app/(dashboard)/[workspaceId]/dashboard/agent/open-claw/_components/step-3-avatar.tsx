"use client";

import { AgentFormData } from "../../_components/types";
import { AvatarSelector } from "../../_components/avatar-selector";

interface Step3Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step3Avatar({ formData, setFormData }: Step3Props) {
    return <AvatarSelector formData={formData} setFormData={setFormData} />;
}
