import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from 'react';

type Credentials = {
  email: string;
  password: string;
};

type AuthContextValue = {
  isSignedIn: boolean;
  signIn: (credentials: Credentials) => Promise<boolean>;
  signUp: (credentials: Credentials) => Promise<boolean>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [isSignedIn, setIsSignedIn] = useState(false);

  const signIn = useCallback(async (_credentials: Credentials) => {
    // TODO: Replace with real API call.
    setIsSignedIn(true);
    return true;
  }, []);

  const signUp = useCallback(async (_credentials: Credentials) => {
    // TODO: Replace with real API call.
    setIsSignedIn(true);
    return true;
  }, []);

  const signOut = useCallback(() => {
    setIsSignedIn(false);
  }, []);

  const value = useMemo(
    () => ({
      isSignedIn,
      signIn,
      signUp,
      signOut,
    }),
    [isSignedIn, signIn, signUp, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
