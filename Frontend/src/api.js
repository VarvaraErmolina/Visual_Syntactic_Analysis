const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export async function getOptions() {
  const response = await fetch(`${API_BASE_URL}/api/options`)

  if (!response.ok) {
    throw new Error('Не удалось загрузить опции фильтров')
  }

  return await response.json()
}

export async function analyze(payload) {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка анализа')
  }

  return await response.json()
}
export async function getExamplesSummary(payload) {
  const response = await fetch(`${API_BASE_URL}/api/examples/summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка загрузки сводки примеров')
  }

  return await response.json()
}


export async function getExamples(payload) {
  const response = await fetch(`${API_BASE_URL}/api/examples`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка загрузки примеров')
  }

  return await response.json()
}