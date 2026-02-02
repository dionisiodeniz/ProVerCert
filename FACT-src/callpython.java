import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.FileWriter;

public class callpython {

    public double [] execPython(String cmString){
        double [] ret = new double[0];
            try {
                FileWriter writer = new FileWriter("tmp.py");
                writer.write(cmString);
                writer.close();
                ProcessBuilder pb = new ProcessBuilder("python", "tmp.py");
                Process p = pb.start();
                BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    String [] twoparts = line.split(":");
                    String [] twonumbs = twoparts[1].split(",");
                    if (twoparts[0].equalsIgnoreCase("ok")){
                        ret = new double[]{Double.parseDouble(twonumbs[0]),Double.parseDouble(twonumbs[1])};
                    }
                    System.out.println("python: result: "+twoparts[0]+" args: "+twonumbs[0]+" and "+twonumbs[1]);
                }
                int exitCode = p.waitFor();
                System.out.println("Python script exited with code: " + exitCode);

            } catch (Exception e) {
                e.printStackTrace();
            }

        return ret;
    }

    public static void main(String args[]){
            callpython cp = new callpython();

            double [] ret = cp.execPython("print('ok: 1.0, 2.3')\n");

            System.out.println("got : "+ret[0]+","+ret[1]+" back");
        }
}
