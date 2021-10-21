# meek

## How

```
⌘ python scripts/cli.py 
> help
  complete: Mark activities as complete.
     debug: Change logging level to DEBUG
    delete: Delete indicated activities.
       due: List unfinished activities by due date.
     error: Change logging level to ERROR
      full: Display all information for indicated activities.
      help: Get help with available commands.
      info: Change logging level to INFO
     level: Get the current logging level.
      list: List activities.
      load: Load activities from storage.
    modify: Make modifications to selected activities.
       new: Create a new activity.
   overdue: List unfinished activities by due date (including those previously due)
     purge: Clear all activities and indexes.
      quit: Quit interactive interface.
reschedule: Reschedule a "due" activity.
      save: Save activities to storage.
   warning: Change logging level to WARNING
> help new
Create a new activity.
    > new
      creates a new, empty activity
    > new Take a nap
      creates a new activity with title "Take a nap"
    > new Take a nap due=today
    > new Take a nap due:today
    > new Take a nap due:2021-07-03
    > new Take a nap due:'next monday'
    > new Take a nap tags=personal,home,health
Aliases: n
>
```

## Next

- Add "previous" as a filter word for due listing (what did I mean by this?)
- Add 'events today' function (and similar) using tag:event
- Add 'errands today' function (and similar) using tag:errand
- Add support for event completion history (last week, last month, etc.)
- Export to markdown
- add start/end times to activities tagged "event"? and add functions around that?
- add "not" filter for listings, e.g., "due this week not today" or "due this week not:today" or "due this week not(due:today") -- I like the last of these syntaxes
- auto-prune history on daily and weekly activities leaving only most recent cycle of completion (keep history and JSON from getting too huge)

