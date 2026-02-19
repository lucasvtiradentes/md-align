## tables - col mismatch

| Service    | Usage                        |
|------------|------------------------------|
| Linear API | Status transitions, comments |
| GitHub API | Repo clone, PR creation      |

## tables - cell spacing

| Name | Type   |
|------|--------|
| foo  | string |

## box-widths - trailing space + border vs content

```
┌───────────────┐
│  Linear UI    │
│  (userscript) │
└───────────────┘
```

```
┌──────────┐
│ content  │
│ text     │
└──────────┘
```

## box-widths - trailing spaces after box

```
┌──────────┐    step    ┌───────────┐
│ Source   │───────────>│ Result.js │
│ (input)  │            │ (output)  │
└──────────┘            └───────────┘
```

## rails - column drift

```
┌──────┬──────┐
│      │      │
│      │      │
│      │      │
└──────┴──────┘
```

## rails - multi box border mismatch

```
┌────────────────────┐    ┌─────────────────────────┐
│ SecurityMiddleware │───>│ ErrorConvertInterceptor │
│ (HSTS, Helmet)     │    │ (error normalization)   │
└────────────────────┘    └─────────────────────────┘
```

## arrows - v arrow shift

```
┌──────┬──────┐
│      │      │
└──────┴──────┘
       v 
```

## pipes - pipe drift

```
┌──────┬──────┐
│      │      │
└──────┴──────┘
       │ 
```

## box-walls - short wall

```
┌──────────────────┐
│  content here    │
│  more text       │
└──────────────────┘
```

## box-walls - inner displaced

```
┌──────────────────────┐
│  outer content       │
│                      │
│  ┌──────────────┐    │
│  │  inner box   │    │
│  │  with text   │    │
│  └──────────────┘    │
│                      │
└──────────────────────┘
```

## box-walls - nested cascade

```
┌──────────────────────────────┐
│  outer                       │
│                              │
│  ┌────────────────────┐      │
│  │  inner             │      │
│  │                    │      │
│  └────────────────────┘      │
│                              │
└──────────────────────────────┘
```

## box-walls - displaced closing row

```
┌──────────┐   step one   ┌──────────┐   step two   ┌──────────┐
│ Source   │─────────────>│ Process  │─────────────>│ Output   │
│          │              │          │              │          │
└──────────┘              └──────────┘              └──┬───────┘
                                                       │
                                                  ┌────v────┐
                                                  │ Result  │
                                                  └─────────┘
```

## box-walls - displaced closing row right

```
┌──────────┐   label one   ┌──────────┐   label two   ┌──────────┐
│ Alpha    │──────────────>│ Beta     │──────────────>│ Gamma    │
│          │               │          │               │          │
└──────────┘               └──────────┘               └──────────┘
```

## list-descs - basic

related docs:
- docs/repo.md                    - local tooling that mirrors CI steps
- docs/guides/testing-strategy.md - test suite run by CI

related sources:
- .github/workflows/callable-ci.yml  - reusable CI workflow definition
- .github/workflows/prs.yml          - PR trigger workflow
- .github/workflows/push-to-main.yml - main branch trigger workflow

## general - pipeline with merge (rails + arrows + pipes + box-widths)

```
┌───────────────────────────────────────────────────────┐
│                  CI Pipeline                          │
│                                                       │
│  ┌──────────┐   ┌──────────┐                          │
│  │ lint     │   │ test     │                          │
│  └────┬─────┘   └────┬─────┘                          │
│       │              │                                │
│       └──────┬───────┘                                │
│              v                                        │
│       ┌──────────┐                                    │
│       │  deploy  │                                    │
│       └──────────┘                                    │
└───────────────────────────────────────────────────────┘
```

## general - deep nested (box-walls + rails + arrows + box-widths)

```
┌──────────────────────────────────────────────────────────────┐
│                      Authentication                          │
│                                                              │
│  ┌────────────┐   Bearer token   ┌──────────────┐            │
│  │ Userscript │─────────────────>│ validateAuth │            │
│  │            │                  │ compare with │            │
│  └────────────┘                  └──────────────┘            │
│                                                              │
│  ┌────────────┐   OIDC token     ┌──────────────┐            │
│  │ GitHub     │─────────────────>│ Workload     │            │
│  │ Actions    │                  │ Identity Fed │            │
│  └────────────┘                  └────┬─────────┘            │
│                                       v                      │
│                                ┌──────────────┐              │
│                                │ deployer SA  │              │
│                                └──────────────┘              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## general - tree inside box (box-widths trailing spaces)

```
┌─────────────────────────────────────────────────┐
│  VM Startup & Execution                         │
│                                                 │
│  bootstrap.sh                                   │
│  │                                              │
│  ├── download vm-setup.zip from GCS             │
│  ├── extract to /opt/vm-setup                   │
│  └── exec runner/main.sh                        │
│      │                                          │
│      ├── setup.sh                               │
│      ├── agent.sh                               │
│      └── teardown.sh                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## general - sequence diagram (rails)

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Client   │     │ Server       │     │ Database │
└────┬─────┘     └──────┬───────┘     └────┬─────┘
     │                  │                  │
     │  POST /api       │                  │
     │────────────────> │                  │
     │                  │  SELECT *        │
     │                  │────────────────> │
     │                  │                  │
     │  { data }        │                  │
     │<─────────────────│                  │
```

## general - branching flow (rails + arrows)

```
┌──────────────┐
│  webhook     │
└──────┬───────┘
       │
       ┌───────────────┼───────────────┐
       v               v               v
┌────────────┐   ┌───────────┐   ┌────────────┐
│ Firestore  │   │ Compute   │   │ Storage    │
│ store run  │   │ create VM │   │ fetch zip  │
└────────────┘   └───────────┘   └────────────┘
```

## general - mixed (tables + box-walls)

| Name | Type |
|------|------|
| foo  | bar  |

```
┌──────────────────┐
│  content here    │
│  more text       │
└──────────────────┘
```

## box-padding - inconsistent left pad

```
┌──────────────┐
│ validateAuth │
│ compare with │
└──────────────┘
```

## horiz-arrows - right gap

```
┌──────┐          ┌──────┐
│ Src  │─────────>│ Dest │
└──────┘          └──────┘
```

## horiz-arrows - left gap

```
┌──────┐          ┌──────┐
│ Dest │<─────────│ Src  │
└──────┘          └──────┘
```

## box-spacing - content touching wall

```
┌────────────┐
│  errors[]  │
│  (strings) │
└────────────┘
```

## def-lists - basic

config:
- timeout:         30s
- retries:         3
- max-connections: 100

## wide-chars - wide chars in diagram

```
┌──────────┐
│ ▶ start  │
│ ● status │
└──────────┘
```
