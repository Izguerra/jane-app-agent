import { NextRequest, NextResponse } from 'next/server';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string; path: string[] }> }
) {
    const { workspaceId, path } = await params;
    const backendUrl = `http://localhost:8000/api/workspaces/${workspaceId}/knowledge-base/${path.join('/')}`;

    try {
        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Cookie': request.headers.get('cookie') || '',
            },
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        return NextResponse.json(
            { error: 'Failed to fetch from backend' },
            { status: 500 }
        );
    }
}

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string; path: string[] }> }
) {
    const { workspaceId, path } = await params;
    const backendUrl = `http://localhost:8000/api/workspaces/${workspaceId}/knowledge-base/${path.join('/')}`;

    try {
        const contentType = request.headers.get('content-type') || '';

        let body: any;
        const headers: Record<string, string> = {
            'Cookie': request.headers.get('cookie') || '',
        };

        if (contentType.includes('multipart/form-data')) {
            const formData = await request.formData();
            body = formData;
            // Do NOT set Content-Type header for multipart/form-data; fetch will set it with boundary
        } else {
            body = await request.json();
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(body);
        }

        const response = await fetch(backendUrl, {
            method: 'POST',
            headers,
            body,
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        return NextResponse.json(
            { error: 'Failed to post to backend' },
            { status: 500 }
        );
    }
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string; path: string[] }> }
) {
    const { workspaceId, path } = await params;
    const backendUrl = `http://localhost:8000/api/workspaces/${workspaceId}/knowledge-base/${path.join('/')}`;

    try {
        const body = await request.json();
        const response = await fetch(backendUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Cookie': request.headers.get('cookie') || '',
            },
            body: JSON.stringify(body),
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        return NextResponse.json(
            { error: 'Failed to update backend' },
            { status: 500 }
        );
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string; path: string[] }> }
) {
    const { workspaceId, path } = await params;
    const backendUrl = `http://localhost:8000/api/workspaces/${workspaceId}/knowledge-base/${path.join('/')}`;

    try {
        const response = await fetch(backendUrl, {
            method: 'DELETE',
            headers: {
                'Cookie': request.headers.get('cookie') || '',
            },
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        return NextResponse.json(
            { error: 'Failed to delete from backend' },
            { status: 500 }
        );
    }
}
