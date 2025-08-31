export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className = '', ...rest } = props
  return <input className={`border rounded px-3 py-2 ${className}`} {...rest} />
}

