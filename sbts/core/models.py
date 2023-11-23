class CleanOpeManagerMixin:
    '''
    モデルのマネージャークラスで使用する。フィールドの検査(full_clean)
    を行ってから、オブジェクトの挿入を行う。
    '''

    def create_cleanly(self, *args, **kwargs):
        if hasattr(self, 'instance') and hasattr(self, 'field'):
            # RelatedManager
            kwargs[self.field.name] = self.instance
        obj = self.model(*args, **kwargs)
        obj.full_clean()
        return self.create(*args, **kwargs)


class CleanOpeModelMixin:
    '''
    モデルクラスで使用する。フィールドの検査(full_clean)を行ってから、
    オブジェクトの更新を行う。
    '''

    def save_cleanly(self, *args, **kwargs):
        self.full_clean()
        return self.save(*args, **kwargs)
