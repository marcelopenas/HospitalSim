import avatars from './avatars.ts'

export const defaultAvatar = avatars.default
export const maxImageBytes = 65535
export function avatarSource(value: unknown): string {
  const image = typeof value === 'string' && value ? value : defaultAvatar
  const type = image.startsWith('/9j/') ? 'image/jpeg' : image.startsWith('UklGR') ? 'image/webp' : 'image/png'
  return `data:${type};base64,${image}`
}
export async function uploadAvatar(file: File): Promise<string> {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) throw new Error('Choose a PNG, JPEG, or WebP image.')
  if (file.size > 5 * 1024 * 1024) throw new Error('Choose an image smaller than 5 MB.')
  const image = await createImageBitmap(file)
  try {
    const canvas = document.createElement('canvas')
    canvas.width = 256; canvas.height = 256
    const context = canvas.getContext('2d')
    if (!context) throw new Error('This browser cannot prepare an image upload.')
    context.fillStyle = '#ffffff'; context.fillRect(0, 0, 256, 256)
    // Preserve aspect ratio and centre-crop the profile instead of stretching it.
    const scale = Math.max(256 / image.width, 256 / image.height)
    context.drawImage(image, (256 - image.width * scale) / 2, (256 - image.height * scale) / 2, image.width * scale, image.height * scale)
    for (const quality of [0.9, 0.75, 0.6]) {
      const encoded = canvas.toDataURL('image/jpeg', quality).split(',')[1]
      if (Math.floor(encoded.length * 3 / 4) <= maxImageBytes) return encoded
    }
    throw new Error('The resized image is too large. Choose a simpler image.')
  } finally { image.close() }
}
