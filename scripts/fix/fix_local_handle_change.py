import os

file_path = "app/(dashboard)/[workspaceId]/dashboard/agent/_components/step-1-configure.tsx"
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
found = False
inserted = False
for line in lines:
    new_lines.append(line)
    if "export function Step1ConfigureAgent({ formData, setFormData }: StepProps) {" in line and not inserted:
        # Check if handleChange already exists to avoid duplication if run multiple times
        # But this is a simple script. 
        print("Found target line.")
        found = True
        inserted = True
        new_lines.append("\n")
        new_lines.append("    const handleChange = (key: string, value: any) => {\n")
        new_lines.append("        setFormData((prev) => ({ ...prev, [key]: value }));\n")
        new_lines.append("    };\n")

if not found:
    print("Target line NOT found!")
else:
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    print("File updated.")
