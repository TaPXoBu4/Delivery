from dishka import Provider, Scope, provide

from domain.use_cases import UseCases


def create_container(use_cases: UseCases):

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def use_cases(self) -> UseCases:
            return use_cases

    return MyProvider()
