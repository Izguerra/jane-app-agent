import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth/api';

// Force Node.js runtime for file upload support
export const runtime = 'nodejs';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';




export async function GET() {
    try {
        const response = await authenticatedFetch(`${BACKEND_URL}/workspaces/documents`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error:', response.status, errorText);
            return NextResponse.json(
                { error: 'Failed to fetch documents', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error fetching documents:', error);
        return NextResponse.json(
            { error: 'Internal server error', details: error.message },
            { status: 500 }
        );
    }
}

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();

        // Get all files from the form data
        const files = formData.getAll('files');

        console.log(`Received ${files.length} files for upload`);

        if (files.length === 0) {
            return NextResponse.json(
                { error: 'No files provided' },
                { status: 400 }
            );
        }

        // Create a new FormData to forward to backend
        const backendFormData = new FormData();

        // Process each file
        for (const file of files) {
            if (file instanceof File) {
                console.log(`Processing file: ${file.name}, size: ${file.size}, type: ${file.type}`);

                // Convert File to Blob with proper metadata
                const buffer = await file.arrayBuffer();
                const blob = new Blob([buffer], { type: file.type || 'application/octet-stream' });

                // Append as a File-like object with name
                backendFormData.append('files', blob, file.name);
            } else {
                console.warn('Non-file item in formData:', typeof file);
            }
        }

        console.log('Forwarding to backend:', `${BACKEND_URL}/workspaces/documents`);

        // Forward the FormData to the backend
        const response = await authenticatedFetch(`${BACKEND_URL}/workspaces/documents`, {
            method: 'POST',
            body: backendFormData,
        });



        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                const errorText = await response.text();
                console.error('Backend upload error (non-JSON):', response.status, errorText);
                return NextResponse.json(
                    { error: 'Upload failed', details: errorText },
                    { status: response.status }
                );
            }
            console.error('Backend upload error:', response.status, JSON.stringify(errorData, null, 2));
            return NextResponse.json(
                errorData,
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('Upload successful:', data);
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error uploading documents:', error);
        console.error('Error stack:', error.stack);
        return NextResponse.json(
            { error: 'Failed to upload documents', details: error.message },
            { status: 500 }
        );
    }
}
