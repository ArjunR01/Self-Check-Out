export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { className = '', ...rest } = props
  return <button className={`px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 ${className}`} {...rest} />
}

