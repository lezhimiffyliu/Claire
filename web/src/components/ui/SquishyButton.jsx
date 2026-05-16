function SquishyButton({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = '',
}) {
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
    // Legacy support
    green: 'btn-secondary',
    gray: 'btn-ghost',
  }

  const buttonClass = variantClasses[variant] || variantClasses.primary
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : ''

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${buttonClass} ${disabledClasses} ${className}`}
    >
      {children}
    </button>
  )
}

export default SquishyButton
