---
type: todos
title: To-dos
---
# To-dos

Live view of every open checkbox in the vault (needs the **Tasks** community plugin).
Format: `- [ ] text #todo/<category> 📅 YYYY-MM-DD`

## Overdue
```tasks
not done
due before today
sort by due
```

## Follow-ups owed to people
```tasks
not done
tags include #todo/follow-up
sort by due
```

## Reviews (PRs / docs)
```tasks
not done
tags include #todo/review
sort by due
```

## Tickets
```tasks
not done
tags include #todo/ticket
sort by due
```

## Project work
```tasks
not done
tags include #todo/project
group by filename
```

## Ideas to explore
```tasks
not done
tags include #todo/idea
```

## Growth
```tasks
not done
tags include #todo/growth
```

## Cancelled
```tasks
status.type is CANCELLED
sort by done reverse
limit 20
```
