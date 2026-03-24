import { describe, it, expect } from 'vitest'

describe('Utils', () => {
  describe('Basic', () => {
    it('should pass basic assertion', () => {
      expect(1 + 1).toBe(2)
    })

    it('should handle string operations', () => {
      expect('hello world').toContain('hello')
      expect('hello world').toHaveLength(11)
    })

    it('should handle array operations', () => {
      const arr = [1, 2, 3]
      expect(arr).toHaveLength(3)
      expect(arr).toContain(2)
    })
  })
})
