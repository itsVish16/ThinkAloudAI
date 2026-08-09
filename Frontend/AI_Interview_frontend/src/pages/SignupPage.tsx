import React, { useState } from 'react';
import { EnvelopeSimple, LockKey, Eye, EyeClosed, ShieldWarning, ArrowRight, User, GoogleLogo, GithubLogo, LinkedinLogo, CheckCircle } from '@phosphor-icons/react';
import { authService } from '../services/authService';
import { AuthLayout } from '../components/AuthLayout';

interface SignupPageProps {
  onNavigate: (page: string) => void;
  onSignupSuccess: (tokens: { access_token: string, refresh_token: string }, user: any) => void;
}

export const SignupPage: React.FC<SignupPageProps> = ({ onNavigate, onSignupSuccess }) => {
  const [step, setStep] = useState<'signup' | 'verify'>('signup');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !firstName) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const usernameBase = email.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '');
      const username = `${usernameBase}${Math.floor(Math.random() * 1000)}`.substring(0, 30);
      const fullName = `${firstName} ${lastName}`.trim();
      
      await authService.signup({ 
        email, 
        password, 
        username,
        full_name: fullName 
      });
      
      setSuccessMessage('Account created! Please check your email for the verification code.');
      setStep('verify');
    } catch (err: any) {
      if (err.message?.toLowerCase().includes('already registered')) {
        setErrorMessage('This email is already registered and verified. Please log in instead.');
      } else {
        setErrorMessage(err.message || 'An error occurred during registration.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !otp) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await authService.verifyEmail(email, otp);
      
      // Automatically login after successful verification
      const loginRes = await authService.login(email, password);
      const token = loginRes.access_token;
      
      // Fetch profile
      const userProfile = await authService.getMe(token);
      
      onSignupSuccess(loginRes, userProfile);
      onNavigate('dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (!email) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await authService.resendVerification(email);
      setSuccessMessage('A new verification code has been sent to your email.');
      setStep('verify');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to resend verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout onNavigate={onNavigate}>
      <div className="auth-card">
        {/* Tabs - Only show on signup step */}
        {step === 'signup' && (
          <div className="auth-tabs">
            <button className="auth-tab" onClick={() => onNavigate('login')}>Log in</button>
            <button className="auth-tab active">Sign up</button>
          </div>
        )}

        <div className="auth-card-header">
          <h2>{step === 'signup' ? 'Create an account ✨' : 'Verify your email ✉️'}</h2>
          <p>{step === 'signup' 
            ? 'Join ThinkAloudAI to prepare for your next big interview.' 
            : `We sent a 6-digit code to ${email}`}</p>
        </div>

        {errorMessage && (
          <div className="auth-error-banner">
            <ShieldWarning size={18} weight="fill" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="auth-error-banner" style={{ backgroundColor: 'rgba(52, 211, 153, 0.1)', color: '#34d399', borderLeftColor: '#34d399' }}>
            <CheckCircle size={18} weight="fill" />
            <span>{successMessage}</span>
          </div>
        )}

        {step === 'signup' && (
          <>
            <div className="auth-social-row">
              <button className="auth-social-btn" onClick={() => alert('Social Sign Up coming soon!')} title="Continue with Google">
                <GoogleLogo weight="bold" className="social-icon" style={{color: '#EA4335'}} />
              </button>
              <button className="auth-social-btn" onClick={() => alert('Social Sign Up coming soon!')} title="Continue with GitHub">
                <GithubLogo weight="fill" className="social-icon" />
              </button>
              <button className="auth-social-btn" onClick={() => alert('Social Sign Up coming soon!')} title="Continue with LinkedIn">
                <LinkedinLogo weight="fill" className="social-icon" style={{color: '#0A66C2'}} />
              </button>
            </div>

            <div className="auth-divider">or</div>

            <form onSubmit={handleSignupSubmit} className="auth-form">
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div className="auth-input-group" style={{ flex: 1 }}>
                  <label className="auth-label">First name</label>
                  <div className="input-wrapper">
                    <User weight="duotone" className="input-icon" size={20} />
                    <input
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      placeholder="John"
                      className="auth-input-field"
                      required
                      disabled={isLoading}
                    />
                  </div>
                </div>
                <div className="auth-input-group" style={{ flex: 1 }}>
                  <label className="auth-label">Last name</label>
                  <div className="input-wrapper">
                    <User weight="duotone" className="input-icon" size={20} />
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder="Doe"
                      className="auth-input-field"
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>

              <div className="auth-input-group">
                <label className="auth-label">Email address</label>
                <div className="input-wrapper">
                  <EnvelopeSimple weight="duotone" className="input-icon" size={20} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="auth-input-group">
                <label className="auth-label">Password</label>
                <div className="input-wrapper">
                  <LockKey weight="duotone" className="input-icon" size={20} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Create a password"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                  <button 
                    type="button" 
                    className="toggle-password-btn"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <Eye size={18} /> : <EyeClosed size={18} />}
                  </button>
                </div>
              </div>

              <button 
                type="submit" 
                className="auth-submit-btn"
                disabled={isLoading || !email || !password || !firstName}
              >
                {isLoading ? (
                  <div className="spinner-mini"></div>
                ) : (
                  <>Sign up <ArrowRight size={18} weight="bold" /></>
                )}
              </button>
            </form>

            <div className="auth-redirect" style={{ marginTop: '1rem', flexDirection: 'column', gap: '0.5rem' }}>
              <div>Already have an account? <span onClick={() => onNavigate('login')} className="auth-link">Log in</span></div>
            </div>
          </>
        )}

        {step === 'verify' && (
          <>
            <form onSubmit={handleVerifySubmit} className="auth-form">
              <div className="auth-input-group">
                <label className="auth-label">Verification Code (6 Digits)</label>
                <div className="input-wrapper">
                  <LockKey weight="duotone" className="input-icon" size={20} />
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="123456"
                    className="auth-input-field"
                    maxLength={6}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <button 
                type="submit" 
                className="auth-submit-btn"
                disabled={isLoading || otp.length !== 6}
              >
                {isLoading ? (
                  <div className="spinner-mini"></div>
                ) : (
                  <>Verify & Login <ArrowRight size={18} weight="bold" /></>
                )}
              </button>
            </form>

            <div className="auth-redirect" style={{ marginTop: '1rem', flexDirection: 'column', gap: '0.5rem' }}>
              <div>Didn't receive a code? <span onClick={handleResendOtp} className="auth-link">Resend it</span></div>
              <div><span onClick={() => setStep('signup')} className="auth-link">Back to Sign up</span></div>
            </div>
          </>
        )}
      </div>
    </AuthLayout>
  );
};
export default SignupPage;
