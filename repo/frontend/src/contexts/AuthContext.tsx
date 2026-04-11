import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import type { User, LoginRequest } from "@/api/types/auth.types";
import * as authApi from "@/api/endpoints/auth";
import { useIdleTimer } from "@/hooks/useIdleTimer";

// ---------- State ----------
interface AuthState {
  user: User | null;
  isLoading: boolean;
  idleWarningVisible: boolean;
  reauthRequired: boolean;
}

const initialState: AuthState = {
  user: null,
  isLoading: true,
  idleWarningVisible: false,
  reauthRequired: false,
};

// ---------- Actions ----------
type AuthAction =
  | { type: "LOGIN_SUCCESS"; payload: User }
  | { type: "LOGOUT" }
  | { type: "IDLE_WARNING" }
  | { type: "IDLE_EXTEND" }
  | { type: "IDLE_EXPIRE" }
  | { type: "REAUTH_SUCCESS"; payload: User }
  | { type: "SET_LOADING"; payload: boolean };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "LOGIN_SUCCESS":
      return {
        ...state,
        user: action.payload,
        isLoading: false,
        idleWarningVisible: false,
        reauthRequired: false,
      };
    case "LOGOUT":
      return {
        ...state,
        user: null,
        isLoading: false,
        idleWarningVisible: false,
        reauthRequired: false,
      };
    case "IDLE_WARNING":
      return { ...state, idleWarningVisible: true };
    case "IDLE_EXTEND":
      return { ...state, idleWarningVisible: false };
    case "IDLE_EXPIRE":
      return {
        ...state,
        idleWarningVisible: false,
        reauthRequired: true,
      };
    case "REAUTH_SUCCESS":
      return {
        ...state,
        user: action.payload,
        reauthRequired: false,
        idleWarningVisible: false,
      };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    default:
      return state;
  }
}

// ---------- Context ----------
interface AuthContextValue extends AuthState {
  login: (data: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  dispatch: React.Dispatch<AuthAction>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ---------- Provider ----------
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing session on mount
  useEffect(() => {
    let cancelled = false;
    async function checkSession() {
      try {
        const session = await authApi.getSession();
        if (!cancelled) {
          dispatch({ type: "LOGIN_SUCCESS", payload: session.user });
        }
      } catch {
        if (!cancelled) {
          dispatch({ type: "LOGOUT" });
        }
      }
    }
    checkSession();
    return () => {
      cancelled = true;
    };
  }, []);

  // Listen for session-expired events from the API client
  useEffect(() => {
    const handler = () => {
      dispatch({ type: "IDLE_EXPIRE" });
    };
    window.addEventListener("auth:session-expired", handler);
    return () => window.removeEventListener("auth:session-expired", handler);
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    dispatch({ type: "SET_LOADING", payload: true });
    try {
      const response = await authApi.login(data);
      dispatch({ type: "LOGIN_SUCCESS", payload: response.user });
    } catch (error) {
      dispatch({ type: "SET_LOADING", payload: false });
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Even if the API call fails, clear local state
    } finally {
      dispatch({ type: "LOGOUT" });
    }
  }, []);

  // ── Idle timer: warns at 13 min, expires at 15 min ──
  const handleIdleWarning = useCallback(() => {
    dispatch({ type: "IDLE_WARNING" });
  }, []);

  const handleIdleExpire = useCallback(() => {
    dispatch({ type: "IDLE_EXPIRE" });
  }, []);

  useIdleTimer({
    onWarning: handleIdleWarning,
    onExpire: handleIdleExpire,
    enabled: !!state.user && !state.reauthRequired,
  });

  return (
    <AuthContext.Provider value={{ ...state, login, logout, dispatch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export { AuthContext };
