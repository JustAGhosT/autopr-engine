self.on_recovery_callbacks: list[
    Callable[
        [ErrorInfo, ErrorRecoveryStrategy],
        None
    ]
] = []