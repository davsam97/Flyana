/* Turns achievement codes sent by the API into toasts.
 *
 * Call it from a component's setup: `useI18n` needs the component context,
 * so the returned `announce` keeps working later from any callback.
 */
export function useAchievements() {
  const { t } = useI18n()
  const { push } = useToast()

  function announce(codes: string[]) {
    for (const code of codes) {
      push({
        title: t('toast.achievementUnlocked'),
        body: t(`achievements.${code}.name`),
        emoji: ACHIEVEMENT_ICONS[code] ?? '🏅',
      })
    }
  }

  return { announce }
}
