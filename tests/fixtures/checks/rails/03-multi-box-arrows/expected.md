```
┌────────────────────┐    ┌─────────────────────────┐
│ SecurityMiddleware │───>│ ErrorConvertInterceptor │
│ (HSTS, Helmet)     │    │ (error normalization)   │
└────────────────────┘    └─────────────────────────┘
```
