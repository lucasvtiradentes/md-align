```
┌─────────────────────────────────────────────────────┐
│  VM Startup & Execution                             │ 
│                                                     │
│  bootstrap.sh                                       │
│  │                                                  │
│  ├── download vm-setup.zip from GCS                 │ 
│  ├── extract to /opt/vm-setup                       │
│  └── exec runner/main.sh                            │
│      │                                              │ 
│      ├── setup.sh                                   │
│      ├── agent.sh                                   │
│      └── teardown.sh                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```
