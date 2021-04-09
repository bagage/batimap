import { Component, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';

@Component({
    template: '',
})
/* eslint-disable */
export class Unsubscriber implements OnDestroy {
    private readonly subscriptions: Subscription[] = [];

    autoUnsubscribe(subscription: Subscription) {
        this.subscriptions.push(subscription);
    }
    ngOnDestroy(): void {
        this.subscriptions.forEach(it => it.unsubscribe());
    }
}
