package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.config.OperationsProperties;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.PosixFilePermission;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import tools.jackson.core.JacksonException;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

@Component
public class ControlFileStore {
    private static final TypeReference<Map<String,Object>> MAP=new TypeReference<>() { };
    private static final Set<PosixFilePermission> PRIVATE=Set.of(PosixFilePermission.OWNER_READ,PosixFilePermission.OWNER_WRITE);
    private final Path root;
    private final ObjectMapper json;

    public ControlFileStore(OperationsProperties properties,ObjectMapper json){
        this.root=properties.controlRoot().toAbsolutePath().normalize();this.json=json;
    }

    public Map<String,Object> readStatus(String name){return read(path("status",name));}
    public Map<String,Object> readRequest(String name){return read(path("inbox",name));}
    public boolean requestExists(String name){return Files.isRegularFile(path("inbox",name));}

    public void publishRequest(String name,Map<String,Object> payload){
        Path inbox=path("inbox",name).getParent();Path target=inbox.resolve(name);Path temporary=null;
        try{
            Files.createDirectories(inbox);
            if(Files.isSymbolicLink(inbox)||Files.isSymbolicLink(root)) throw new IllegalStateException("Control directories must not be symbolic links.");
            temporary=Files.createTempFile(inbox,"."+name+".",".tmp");
            setPrivate(temporary);
            byte[] bytes=(json.writerWithDefaultPrettyPrinter().writeValueAsString(payload)+"\n").getBytes(StandardCharsets.UTF_8);
            try(FileChannel channel=FileChannel.open(temporary,StandardOpenOption.WRITE,StandardOpenOption.TRUNCATE_EXISTING)){
                channel.write(ByteBuffer.wrap(bytes));channel.force(true);
            }
            Files.createLink(target,temporary);
            Files.delete(temporary);
            temporary=null;
            setPrivate(target);fsyncDirectory(inbox);
        }catch(java.nio.file.FileAlreadyExistsException exception){throw new ControlConflictException("A host operation is already queued or running.",exception);
        }catch(IOException|JacksonException exception){throw new IllegalStateException("Could not publish host-control request.",exception);
        }finally{if(temporary!=null)try{Files.deleteIfExists(temporary);}catch(IOException ignored){ }}
    }

    private Map<String,Object> read(Path file){
        if(!Files.isRegularFile(file)||Files.isSymbolicLink(file))return Map.of();
        try{return json.readValue(Files.readString(file,StandardCharsets.UTF_8),MAP);}catch(IOException|JacksonException exception){return Map.of();}
    }
    private Path path(String directory,String name){
        if(!name.matches("[a-z0-9-]+\\.(?:json|request)"))throw new IllegalArgumentException("Invalid control-file name.");
        Path result=root.resolve(directory).resolve(name).normalize();
        if(!result.startsWith(root))throw new IllegalArgumentException("Invalid control-file path.");return result;
    }
    private static void setPrivate(Path file){try{Files.setPosixFilePermissions(file,PRIVATE);}catch(IOException|UnsupportedOperationException ignored){ }}
    private static void fsyncDirectory(Path directory){try(FileChannel channel=FileChannel.open(directory,StandardOpenOption.READ)){channel.force(true);}catch(IOException|UnsupportedOperationException ignored){ }}

    public static final class ControlConflictException extends RuntimeException{
        public ControlConflictException(String message,Throwable cause){super(message,cause);}
    }
}
