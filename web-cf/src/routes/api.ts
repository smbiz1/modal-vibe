import { Hono } from 'hono'

const apiRoute = new Hono<{
  Bindings: {
    MODAL_API_URL: string
    API_KEY: string
  }
}>()

// Proxy API requests to Modal backend
apiRoute.all('/:path{.+}', async (c) => {
  const path = c.req.param('path')
  const modalUrl = `${c.env.MODAL_API_URL}/api/${path}`

  try {
    // Forward the request to Modal
    const response = await fetch(modalUrl, {
      method: c.req.method,
      headers: {
        ...Object.fromEntries(c.req.raw.headers),
        // Add API key if needed
        'Authorization': `Bearer ${c.env.API_KEY}`,
        // Remove host header to avoid conflicts
        'host': new URL(modalUrl).host
      },
      body: c.req.method !== 'GET' && c.req.method !== 'HEAD'
        ? await c.req.blob()
        : undefined
    })

    // Return the response
    return c.body(response.body, {
      status: response.status,
      headers: {
        ...Object.fromEntries(response.headers),
        // Ensure CORS headers are set
        'Access-Control-Allow-Origin': c.req.header('origin') || '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      }
    })
  } catch (error) {
    console.error('API proxy error:', error)
    return c.json({ error: 'Service temporarily unavailable' }, 503)
  }
})

// Handle OPTIONS requests for CORS preflight
apiRoute.options('/:path{.+}', (c) => {
  return c.newResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': c.req.header('origin') || '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
  })
})

export { apiRoute }
