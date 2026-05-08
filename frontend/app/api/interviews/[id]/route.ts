import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// Next.js 15: params is a Promise and must be awaited
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const auth = request.headers.get('Authorization') || '';
        const response = await fetch(`${BACKEND_URL}/interviews/${id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': auth,
            },
        });

        if (!response.ok) {
            return NextResponse.json({ error: `Failed: ${response.status}` }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const auth = request.headers.get('Authorization') || '';
        const body = await request.json();
        const response = await fetch(`${BACKEND_URL}/interviews/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': auth,
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            return NextResponse.json({ error: `Failed: ${response.status}` }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const auth = request.headers.get('Authorization') || '';
        const response = await fetch(`${BACKEND_URL}/interviews/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': auth,
            },
        });

        if (!response.ok && response.status !== 204) {
            return NextResponse.json({ error: `Failed: ${response.status}` }, { status: response.status });
        }

        // Backend returns 204 No Content — propagate as-is.
        return new NextResponse(null, { status: 204 });
    } catch {
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

