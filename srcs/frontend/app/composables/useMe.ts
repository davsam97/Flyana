export function useMe() {
  const { user, fetchMe } = useAuth()
  return { me: user, load: () => fetchMe() }
}
