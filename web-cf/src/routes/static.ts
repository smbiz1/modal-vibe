import { Hono } from 'hono'

const staticRoute = new Hono<{ Bindings: { STATIC_BUCKET: R2Bucket } }>()

// Serve static files from R2 bucket
staticRoute.get('/:filename{.+}', async (c) => {
  const filename = c.req.param('filename')
  const object = await c.env.STATIC_BUCKET.get(filename)

  if (!object) {
    return c.notFound()
  }

  const contentType = getContentType(filename)
  return c.body(object.body, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=31536000', // 1 year cache
    }
  })
})

function getContentType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const types: Record<string, string> = {
    'css': 'text/css',
    'js': 'application/javascript',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon',
    'woff': 'font/woff',
    'woff2': 'font/woff2'
  }
  return types[ext || ''] || 'application/octet-stream'
}

export { staticRoute }
