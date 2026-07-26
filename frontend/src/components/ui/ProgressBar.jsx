function ProgressBar({ current, total }) {
  const progress = (current / total) * 100

  return (
    <div className="progress-bar w-full max-w-md mx-auto">
      <div
        className="progress-bar-fill"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}

export default ProgressBar
