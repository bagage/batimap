import {
    HttpErrorResponse,
    HttpEvent,
    HttpHandler,
    HttpHeaders,
    HttpInterceptor,
    HttpRequest,
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarRef, SimpleSnackBar } from '@angular/material/snack-bar';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class HttpErrorInterceptor implements HttpInterceptor {
    static BYPASS_HEADER = 'No-Http-Error-Interceptor';
    private ref?: MatSnackBarRef<SimpleSnackBar> = undefined;

    static ByPassInterceptor(): { headers: HttpHeaders } {
        let headers = new HttpHeaders();
        headers = headers.set(HttpErrorInterceptor.BYPASS_HEADER, 'bypass1');

        return { headers };
    }

    constructor(private readonly snackbar: MatSnackBar) {}
    // tslint:disable
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        const shouldBypass = request.headers.has(HttpErrorInterceptor.BYPASS_HEADER);
        let forwardedRequest = request.clone({ headers: request.headers.delete(HttpErrorInterceptor.BYPASS_HEADER) });

        return next.handle(forwardedRequest).pipe(
            catchError((error: HttpErrorResponse) => {
                if (shouldBypass) {
                    return throwError(error);
                }

                let errorMessage = '';
                if (error.error instanceof ErrorEvent) {
                    // client-side error
                    errorMessage = `Une erreur est survenue : ${error.error.message}.`;
                } else {
                    if (error.status === 0 && error.url) {
                        const host = new URL(error.url);
                        if (host.host === '127.0.0.1:8111') {
                            errorMessage = 'JOSM est injoignable. Est-il toujours lancé ?';
                        } else {
                            // offline or security-related (CORS) issue
                            errorMessage = 'Impossible de contacter le serveur.';
                        }
                    } else {
                        // server-side error
                        errorMessage = `Une erreur serveur (${error.status}) est survenue : ${error.message}. Veuillez réessayer plus tard.`;
                    }
                }

                if (this.ref) {
                    this.ref.dismiss();
                }

                this.ref = this.snackbar.open(errorMessage, 'OK');

                return throwError(errorMessage);
            })
        );
    }
}
