package eu.royalblackwater.api.persistence;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.regex.Pattern;
import org.flywaydb.core.Flyway;

/** One-shot database ownership boundary used before the runtime API starts. */
public final class DatabaseMigrationMain {
    private static final Pattern IDENTIFIER=Pattern.compile("[A-Za-z_][A-Za-z0-9_]{1,31}");
    private static final Path SECRETS=Path.of("/run/secrets");

    private DatabaseMigrationMain(){ }

    public static void main(String[] args) throws Exception{
        String url=requiredEnvironment("DATABASE_URL");
        String owner=identifier(requiredEnvironment("DATABASE_OWNER_USER"));
        String application=identifier(requiredEnvironment("DATABASE_APP_USER"));
        String database=identifier(requiredEnvironment("DATABASE_NAME"));
        String ownerPassword=secret("database.owner.password");
        String applicationPassword=secret("database.app.password");
        try(Connection connection=DriverManager.getConnection(url,owner,ownerPassword)){
            connection.setAutoCommit(true);
            ensureApplicationRole(connection,application,applicationPassword);
        }
        Flyway.configure().dataSource(url,owner,ownerPassword).cleanDisabled(true)
                .validateMigrationNaming(true).load().migrate();
        try(Connection connection=DriverManager.getConnection(url,owner,ownerPassword)){
            connection.setAutoCommit(false);
            grantRuntimeAccess(connection,owner,application,database);
            connection.commit();
        }
        System.out.println("[database] Schema migrated and restricted runtime grants reconciled.");
    }

    private static void ensureApplicationRole(Connection connection,String role,String password)throws SQLException{
        boolean exists;
        try(PreparedStatement query=connection.prepareStatement("select exists(select 1 from pg_roles where rolname=?)")){
            query.setString(1,role);
            try(ResultSet result=query.executeQuery()){result.next();exists=result.getBoolean(1);}
        }
        String quotedRole=quoteIdentifier(connection,role);String quotedPassword=quoteLiteral(connection,password);
        try(Statement statement=connection.createStatement()){
            if(!exists)statement.execute("create role "+quotedRole+" login nosuperuser nocreatedb nocreaterole noinherit password "+quotedPassword);
            else statement.execute("alter role "+quotedRole+" login nosuperuser nocreatedb nocreaterole noinherit password "+quotedPassword);
        }
    }

    private static void grantRuntimeAccess(Connection connection,String owner,String application,String database)throws SQLException{
        String app=quoteIdentifier(connection,application);String ownerRole=quoteIdentifier(connection,owner);
        String db=quoteIdentifier(connection,database);
        try(Statement statement=connection.createStatement()){
            statement.execute("revoke all on database "+db+" from "+app);
            statement.execute("grant connect on database "+db+" to "+app);
            statement.execute("revoke create on schema public from public");
            statement.execute("revoke create on schema public from "+app);
            statement.execute("grant usage on schema public to "+app);
            statement.execute("grant select,insert,update,delete on all tables in schema public to "+app);
            statement.execute("grant usage,select,update on all sequences in schema public to "+app);
            statement.execute("alter default privileges for role "+ownerRole+" in schema public grant select,insert,update,delete on tables to "+app);
            statement.execute("alter default privileges for role "+ownerRole+" in schema public grant usage,select,update on sequences to "+app);
            statement.execute("alter role "+app+" in database "+db+" set search_path=public,pg_catalog");
        }
    }

    private static String quoteIdentifier(Connection connection,String value)throws SQLException{
        return quote(connection,"select quote_ident(?)",value);
    }
    private static String quoteLiteral(Connection connection,String value)throws SQLException{
        return quote(connection,"select quote_literal(?)",value);
    }
    private static String quote(Connection connection,String sql,String value)throws SQLException{
        try(PreparedStatement statement=connection.prepareStatement(sql)){
            statement.setString(1,value);try(ResultSet result=statement.executeQuery()){result.next();return result.getString(1);}
        }
    }
    private static String identifier(String value){
        if(!IDENTIFIER.matcher(value).matches())throw new IllegalArgumentException("Invalid database identifier.");return value;
    }
    private static String requiredEnvironment(String name){
        String value=System.getenv(name);if(value==null||value.isBlank())throw new IllegalStateException("Missing environment: "+name);return value.strip();
    }
    private static String secret(String name)throws IOException{
        String value=Files.readString(SECRETS.resolve(name)).strip();
        if(value.isEmpty())throw new IllegalStateException("Empty database secret: "+name);return value;
    }
}
