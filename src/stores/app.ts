import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const studentName = ref('Aguiluz')

  const modules = ref([
    { id: 1, title: 'Module 1', emoji: '📘', locked: false, status: 'In Progress' },
    { id: 2, title: 'Module 2', emoji: '📗', locked: true,  status: 'Complete prev.' },
    { id: 3, title: 'Module 3', emoji: '📙', locked: true,  status: 'Complete prev.' },
    { id: 4, title: 'Module 4', emoji: '📕', locked: true,  status: 'Complete prev.' },
  ])

  const progressItems = ref([
    { title: 'Science Topic', subtitle: 'starting ideas', lesson: 'Lesson 4 of 12', percent: 38, type: 'topic' },
    { title: 'Video Title',   subtitle: 'starting ideas', lesson: 'Video 6 of 13',  percent: 45, type: 'video' },
  ])

  const deadlines = ref([
    { title: 'Quiz 1 – Science', date: 'Sep 12' },
    { title: 'Module 2 Essay',   date: 'Sep 15' },
    { title: 'Lab Report',      date: 'Sep 20' },
  ])

  return { studentName, modules, progressItems, deadlines }
})
