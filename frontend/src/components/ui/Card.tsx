export function Card(props: React.HTMLAttributes<HTMLDivElement>) {
  const { className = '', ...rest } = props
  return <div className={`bg-white rounded shadow ${className}`} {...rest} />
}

