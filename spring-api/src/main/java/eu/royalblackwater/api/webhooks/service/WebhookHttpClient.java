package eu.royalblackwater.api.webhooks.service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.springframework.stereotype.Component;

@Component
public class WebhookHttpClient {
    private static final int RESPONSE_LIMIT=4096;
    private final HttpClient client;

    public WebhookHttpClient(){
        this(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).followRedirects(HttpClient.Redirect.NEVER).build());
    }
    WebhookHttpClient(HttpClient client){this.client=client;}

    public Result send(String endpoint,String payload) {
        HttpRequest request=HttpRequest.newBuilder(URI.create(endpoint)).timeout(Duration.ofSeconds(10))
                .header("Content-Type","application/json; charset=utf-8")
                .header("User-Agent","RBF-Spring-Webhook/1")
                .POST(HttpRequest.BodyPublishers.ofString(payload)).build();
        try {
            HttpResponse<String> response=client.send(request,HttpResponse.BodyHandlers.ofString());
            String body=response.body()==null?null:response.body().substring(0,Math.min(RESPONSE_LIMIT,response.body().length()));
            return new Result(response.statusCode(),body,response.statusCode()>=200&&response.statusCode()<300,null);
        } catch(InterruptedException exception) {
            Thread.currentThread().interrupt();
            return new Result(null,null,false,"Webhook delivery interrupted.");
        } catch(IOException|IllegalArgumentException exception) {
            return new Result(null,null,false,"Webhook delivery failed: "+exception.getClass().getSimpleName());
        }
    }
    public record Result(Integer status,String body,boolean success,String error){ }
}
