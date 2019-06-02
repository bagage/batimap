import { OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';

export class Unsubscriber implements OnDestroy {
    private readonly subscriptions: Array<Subscription> = [];

    autoUnsubscribe(subscription: Subscription) {
        this.subscriptions.push(subscription);
    }
    ngOnDestroy() {
        this.subscriptions.forEach(it => it.unsubscribe());
    }
}
