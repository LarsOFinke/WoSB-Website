package eu.royalblackwater.api.webhooks;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

import java.net.InetAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

@Component
public class WebhookPolicy {
    private static final Set<String> HOSTS=Set.of("discord.com","www.discord.com","ptb.discord.com","canary.discord.com","discordapp.com");
    private static final Pattern PATH=Pattern.compile("^/api(?:/v\\d{1,2})?/webhooks/[^/\\s]+/[^/\\s]+(?:/(?:github|slack))?/?$",Pattern.CASE_INSENSITIVE);
    private static final Set<String> SCOPES=Set.of("global","fleet","squad");

    public String endpoint(String raw) {
        String value=raw==null?"":raw.strip();
        if(value.startsWith("<")&&value.endsWith(">")&&value.length()>2) value=value.substring(1,value.length()-1).strip();
        try {
            URI uri=new URI(value);
            String host=uri.getHost()==null?"":uri.getHost().toLowerCase(Locale.ROOT).replaceAll("\\.$","");
            int port=uri.getPort();
            if(!"https".equalsIgnoreCase(uri.getScheme())||!HOSTS.contains(host)||uri.getUserInfo()!=null||uri.getFragment()!=null)
                throw bad("Use an official Discord HTTPS webhook URL.");
            if(port!=-1&&port!=443) throw bad("Discord webhooks must use port 443.");
            if(!PATH.matcher(uri.getPath()).matches()) throw bad("Discord webhook URL must contain webhook ID and token.");
            for(InetAddress address:InetAddress.getAllByName(host)) if(!publicAddress(address))
                throw bad("Discord webhook host resolved to a non-public address.");
            return value;
        } catch(URISyntaxException exception) {
            throw bad("Discord webhook URL is invalid.");
        } catch(java.net.UnknownHostException exception) {
            throw bad("Discord webhook host could not be resolved.");
        }
    }

    public List<String> events(List<String> raw,boolean allowEmpty) {
        LinkedHashSet<String> result=new LinkedHashSet<>();
        for(String item:raw==null?List.<String>of():raw) {
            String event=item==null?"":item.strip();
            if(event.isEmpty()) continue;
            if(!WebhookEventCatalog.TYPES.contains(event)) throw bad("Unsupported webhook event type: "+event);
            result.add(event);
        }
        if(result.isEmpty()&&!allowEmpty) throw bad("Select at least one webhook event type.");
        return result.stream().sorted().toList();
    }

    public Scope scope(String raw,Long id) {
        String type=raw==null?"global":raw.strip().toLowerCase(Locale.ROOT);
        if(!SCOPES.contains(type)) throw bad("Unsupported webhook scope.");
        if("global".equals(type)) return new Scope(type,null);
        if(id==null||id<1) throw bad("Fleet and squad webhooks require a scope ID.");
        return new Scope(type,id);
    }

    public String publicEndpoint(String encryptedOrPlain,eu.royalblackwater.api.security.FernetSecretBox secrets) {
        try {
            URI uri=URI.create(endpoint(secrets.decrypt(encryptedOrPlain)));
            String[] parts=uri.getPath().split("/");
            String id=parts.length>0?parts[parts.length-2]:"configured";
            return uri.getScheme()+"://"+uri.getHost()+"/api/webhooks/"+id+"/••••••";
        } catch(RuntimeException exception) {
            return "https://discord.com/api/webhooks/unavailable/••••••";
        }
    }

    private static boolean publicAddress(InetAddress address) {
        byte[] raw=address.getAddress();
        if(address.isAnyLocalAddress()||address.isLoopbackAddress()||address.isLinkLocalAddress()
                ||address.isSiteLocalAddress()||address.isMulticastAddress()) return false;
        return raw.length!=16 || (raw[0]&0xfe)!=0xfc;
    }
    private static ResponseStatusException bad(String message){return new ResponseStatusException(BAD_REQUEST,message);}
    public record Scope(String type,Long id){ }
}
