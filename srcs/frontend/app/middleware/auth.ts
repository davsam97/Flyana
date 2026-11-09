/* `fetchMe(true)` re-checks the server on every navigation instead of
   trusting a stale cached user. */
export default defineNuxtRouteMiddleware(async () => {
  const { fetchMe } = useAuth()
  const me = await fetchMe(true)
  if (!me) return navigateTo('/login')
})
