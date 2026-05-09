import { queryClient } from "@/app/providers";
import { clearCurrentUserCache } from "@/lib/currentUser";
import { disconnectLiveKitSingleton } from "@/hooks/useLiveKitAgent";

const TOKEN_KEY = "ladderflow_token";

// All sessionStorage keys that hold per-user state. Anything user-specific
// must be listed here so logout fully clears it.
const SESSION_KEYS = [
    "agent-config",
    "research-context",
    "research-context-keywords",
    "resume-prior-transcript",
    "pending-review",
    "trending-keywords",
    "selected-topics",
    "selected-angle",
    "selected-angle-id",
    "generated-angle",
    "session-rating",
];

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
    if (typeof window !== "undefined") {
        localStorage.setItem(TOKEN_KEY, token);
    }
}

export function removeToken() {
    if (typeof window !== "undefined") {
        localStorage.removeItem(TOKEN_KEY);
    }
}

export function authHeaders() {
    const token = getToken();
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
}

/**
 * Comprehensive logout — clears EVERY per-user state layer.
 *
 * Without this, a second user on the same browser inherits:
 *   - sessionStorage (interview tokens, transcripts, research context)
 *   - currentUser cache (/api/me response cached for 30s)
 *   - TanStack Query cache (every fetched query)
 *   - LiveKit Room singleton (active room connection + audio elements)
 *
 * Call this from EVERY logout entry point. Do not partially log out.
 */
export async function logout(redirectTo: string = "/login"): Promise<void> {
    // 1. Disconnect any live LiveKit room first (uses token, must run before token removal).
    try {
        await disconnectLiveKitSingleton();
    } catch {
        // non-fatal
    }

    // 2. Clear in-memory caches.
    try {
        clearCurrentUserCache();
    } catch {
        // non-fatal
    }
    try {
        queryClient.clear();
    } catch {
        // non-fatal
    }

    // 3. Clear sessionStorage interview state.
    if (typeof window !== "undefined") {
        for (const key of SESSION_KEYS) {
            try {
                sessionStorage.removeItem(key);
            } catch {
                // non-fatal — storage quota errors etc.
            }
        }
    }

    // 4. Drop auth token last so any error above is still recoverable.
    removeToken();

    // 5. Hard navigate to drop module-level state in any other singletons we
    //    might have missed (defense-in-depth).
    if (typeof window !== "undefined") {
        window.location.href = redirectTo;
    }
}
