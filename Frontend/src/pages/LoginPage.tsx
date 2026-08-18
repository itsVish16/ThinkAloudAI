import React, { useState } from 'react';
import { EnvelopeSimple, LockKey, Eye, EyeClosed, ShieldWarning, ArrowRight, GoogleLogo, GithubLogo, LinkedinLogo, CheckCircle } from '@phosphor-icons/react';
import { authService } from '../services/authService';
import { AuthLayout } from '../components/AuthLayout';

interface LoginPageProps {
  onNavigate: (page: string) => void;
  onLoginSuccess: (tokens: { access_token: string, refresh_token: string }, user: any) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onNavigate, onLoginSuccess }) => {
  const [step, setStep] = useState<'login' | 'forgot_password' | 'reset_password'>('login');
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const loginRes = await authService.login(email, password);
      const token = loginRes.access_token;
      const userProfile = await authService.getMe(token);
      onLoginSuccess(loginRes, userProfile);
      onNavigate('dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred during login.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await authService.forgotPassword(email);
      setSuccessMessage(`Password reset code sent to ${email}`);
      setStep('reset_password');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to request password reset.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !otp || !newPassword) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await authService.resetPassword(email, otp, newPassword);
      setSuccessMessage('Password reset successfully! Logging you in...');
      
      // Auto login
      const loginRes = await authService.login(email, newPassword);
      const token = loginRes.access_token;
      const userProfile = await authService.getMe(token);
      onLoginSuccess(loginRes, userProfile);
      onNavigate('dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired reset code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout onNavigate={onNavigate}>
      <div className="auth-card">
        {/* Segmented Tabs - Only show on login step */}
        {step === 'login' && (
          <div className="auth-tabs-segmented">
            <button className="auth-tab-segment active">Log in</button>
            <button className="auth-tab-segment" onClick={() => onNavigate('signup')}>Sign up</button>
          </div>
        )}

        {/* Card Header */}
        <div className="auth-card-header">
          <h2>
            {step === 'login' && 'Welcome back 👋'}
            {step === 'forgot_password' && 'Reset your password 🔐'}
            {step === 'reset_password' && 'Enter reset code ✉️'}
          </h2>
          <p>
            {step === 'login' && 'Log in to continue your interview preparation journey.'}
            {step === 'forgot_password' && 'Enter your email address and we will send you a 6-digit code.'}
            {step === 'reset_password' && `We sent a 6-digit verification code to ${email}`}
          </p>
        </div>

        {/* Error / Success Notifications */}
        {errorMessage && (
          <div className="auth-banner-error">
            <ShieldWarning size={20} weight="fill" style={{ flexShrink: 0, marginTop: '1px' }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="auth-banner-success">
            <CheckCircle size={20} weight="fill" style={{ flexShrink: 0, marginTop: '1px' }} />
            <span>{successMessage}</span>
          </div>
        )}

        {step === 'login' && (
          <>
            {/* Social Logins */}
            <div className="auth-social-row">
              <button 
                type="button" 
                className="auth-social-btn" 
                onClick={() => alert('Google authentication is configured in production.')} 
                title="Continue with Google"
              >
                <GoogleLogo weight="bold" className="social-icon" style={{ color: '#EA4335' }} />
                <span>Google</span>
              </button>
              <button 
                type="button" 
                className="auth-social-btn" 
                onClick={() => alert('GitHub authentication is configured in production.')} 
                title="Continue with GitHub"
              >
                <GithubLogo weight="fill" className="social-icon" />
                <span>GitHub</span>
              </button>
              <button 
                type="button" 
                className="auth-social-btn" 
                onClick={() => alert('LinkedIn authentication is configured in production.')} 
                title="Continue with LinkedIn"
              >
                <LinkedinLogo weight="fill" className="social-icon" style={{ color: '#0A66C2' }} />
                <span>LinkedIn</span>
              </button>
            </div>

            <div className="auth-divider">or continue with email</div>

            <form onSubmit={handleLoginSubmit} className="auth-form">
              {/* Email Field */}
              <div className="auth-input-group">
                <label className="auth-label">Email address</label>
                <div className="input-wrapper">
                  <EnvelopeSimple weight="duotone" className="input-icon" size={20} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@domain.com"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="auth-input-group">
                <label className="auth-label">Password</label>
                <div className="input-wrapper">
                  <LockKey weight="duotone" className="input-icon" size={20} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                  <button 
                    type="button" 
                    className="toggle-password-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <Eye size={18} /> : <EyeClosed size={18} />}
                  </button>
                </div>
              </div>

              {/* Options Row */}
              <div className="auth-options-row">
                <label className="auth-checkbox-label">
                  <input type="checkbox" className="auth-checkbox" defaultChecked />
                  <span>Remember me</span>
                </label>
                <span 
                  className="forgot-pass-btn" 
                  onClick={() => { setStep('forgot_password'); setErrorMessage(null); setSuccessMessage(null); }}
                >
                  Forgot password?
                </span>
              </div>

              {/* Submit CTA */}
              <button 
                type="submit" 
                className="auth-submit-btn"
                disabled={isLoading || !email || !password}
              >
                {isLoading ? (
                  <div className="spinner-mini" />
                ) : (
                  <>
                    <span>Log in</span>
                    <ArrowRight size={18} weight="bold" />
                  </>
                )}
              </button>
            </form>

            <div className="auth-redirect">
              <span>Don't have an account? <strong onClick={() => onNavigate('signup')} className="auth-link">Sign up</strong></span>
            </div>
          </>
        )}

        {step === 'forgot_password' && (
          <>
            <form onSubmit={handleForgotPasswordSubmit} className="auth-form">
              <div className="auth-input-group">
                <label className="auth-label">Registered email address</label>
                <div className="input-wrapper">
                  <EnvelopeSimple weight="duotone" className="input-icon" size={20} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@domain.com"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <button 
                type="submit" 
                className="auth-submit-btn"
                disabled={isLoading || !email}
              >
                {isLoading ? (
                  <div className="spinner-mini" />
                ) : (
                  <>
                    <span>Send Reset Code</span>
                    <ArrowRight size={18} weight="bold" />
                  </>
                )}
              </button>
            </form>

            <div className="auth-redirect">
              <span onClick={() => { setStep('login'); setErrorMessage(null); setSuccessMessage(null); }} className="auth-link">
                &larr; Back to Log in
              </span>
            </div>
          </>
        )}

        {step === 'reset_password' && (
          <>
            <form onSubmit={handleResetPasswordSubmit} className="auth-form">
              <div className="auth-input-group">
                <label className="auth-label">6-Digit Verification Code</label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    className="auth-input-field auth-otp-input"
                    maxLength={6}
                    required
                    disabled={isLoading}
                    autoFocus
                  />
                </div>
              </div>

              <div className="auth-input-group">
                <label className="auth-label">New Password</label>
                <div className="input-wrapper">
                  <LockKey weight="duotone" className="input-icon" size={20} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Create a strong password"
                    className="auth-input-field"
                    required
                    disabled={isLoading}
                  />
                  <button 
                    type="button" 
                    className="toggle-password-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <Eye size={18} /> : <EyeClosed size={18} />}
                  </button>
                </div>
              </div>

              <button 
                type="submit" 
                className="auth-submit-btn"
                disabled={isLoading || otp.length !== 6 || !newPassword}
              >
                {isLoading ? (
                  <div className="spinner-mini" />
                ) : (
                  <>
                    <span>Reset Password & Log in</span>
                    <ArrowRight size={18} weight="bold" />
                  </>
                )}
              </button>
            </form>

            <div className="auth-redirect">
              <span>Didn't receive a code? <strong onClick={handleForgotPasswordSubmit} className="auth-link">Resend it</strong></span>
              <span onClick={() => { setStep('login'); setErrorMessage(null); setSuccessMessage(null); }} className="auth-link">
                &larr; Back to Log in
              </span>
            </div>
          </>
        )}
      </div>
    </AuthLayout>
  );
};

export default LoginPage;
